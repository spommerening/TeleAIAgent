"""
Ollama Client for Image Analysis
Handles communication with Ollama service for image vision
"""

import asyncio
import base64
import json
import logging
from typing import Dict, List, Optional

import aiohttp

from config import Config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama for image analysis"""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_URL
        self.api_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        
        # Get clean model configuration
        model_config = Config.get_vision_model_config()
        self.primary_model = model_config['primary_model']
        self.fallback_model = model_config['fallback_model']
        self.emergency_fallback = model_config['emergency_fallback']
        
        self.active_model = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the Ollama client and ensure model is available"""
        logger.info(f"🔧 Initializing Ollama client with model chain: {self.primary_model} → {self.fallback_model} → {self.emergency_fallback}, url={self.base_url}")
        
        # Create HTTP session with different timeouts for different operations
        # Model downloads and inference can take very long on CPU-only systems
        self.download_timeout = aiohttp.ClientTimeout(total=Config.OLLAMA_DOWNLOAD_TIMEOUT)
        self.inference_timeout = aiohttp.ClientTimeout(total=Config.OLLAMA_INFERENCE_TIMEOUT)
        self.health_timeout = aiohttp.ClientTimeout(total=Config.OLLAMA_HEALTH_TIMEOUT)
        
        self.session = aiohttp.ClientSession(timeout=self.download_timeout)
        
        try:
            # Check if Ollama service is available
            await self.health_check()
            
            # Ensure model is available
            await self._ensure_model_available()
            
            self.initialized = True
            logger.info("✅ Ollama client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Ollama client: {str(e)}")
            raise
            
    async def _ensure_model_available(self):
        """Ensure the best available model is ready, with intelligent fallback chain"""
        models_to_try = [self.primary_model, self.fallback_model, self.emergency_fallback]
        logger.info(f"🔍 Checking model availability in order: {models_to_try}")
        
        try:
            # List available models
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    available_models = [model['name'] for model in models_data.get('models', [])]
                    
                    # Try models in order of preference
                    for i, model in enumerate(models_to_try):
                        if model in available_models:
                            self.active_model = model
                            status = "✅ primary" if i == 0 else f"⚠️ {'fallback' if i == 1 else 'emergency'}"
                            logger.info(f"{status} vision model available: {self.active_model}")
                            return
                    
            # Try to pull primary model as last resort
            logger.info(f"📥 No vision models available, attempting to pull primary: {self.primary_model}")
            
            pull_data = {"name": self.primary_model}
            async with self.session.post(f"{self.base_url}/api/pull", json=pull_data) as response:
                if response.status == 200:
                    # Stream the download progress
                    async for line in response.content:
                        if line:
                            try:
                                progress_data = json.loads(line)
                                status = progress_data.get('status', '')
                                if 'pulling' in status.lower():
                                    logger.info(f"📥 Download progress: {status}")
                                elif status == 'success':
                                    self.active_model = self.primary_model
                                    logger.info(f"✅ Primary model downloaded successfully: {self.active_model}")
                                    return
                            except json.JSONDecodeError:
                                continue
                else:
                    logger.warning(f"⚠️ Failed to pull primary model, using fallback: {self.fallback_model}")
                    self.active_model = self.fallback_model
                    
        except Exception as e:
            logger.error(f"❌ Model availability check failed: {str(e)}")
            self.active_model = self.fallback_model
            logger.info(f"🔄 Defaulting to fallback model: {self.active_model}")
            
    async def analyze_image(self, image_data: bytes, prompt: Optional[str] = None) -> str:
        """
        Analyze image and generate a comprehensive description using Ollama with health checks
        
        Args:
            image_data: Raw image bytes
            prompt: Optional custom prompt (uses default if not provided)
            
        Returns:
            String with comprehensive image description
        """
        if not self.initialized or not self.session:
            raise Exception("Ollama client not initialized")
            
        # Use default German description prompt if none provided
        if prompt is None:
            prompt = "Beschreibe dieses Bild detailliert auf Deutsch, einschließlich Objekten, Personen, Umgebung, Farben, Stimmung und bemerkenswerten Eigenschaften. Gib eine umfassende Beschreibung in 2-3 Sätzen."
            
        logger.info(f"🔍 Analyzing image with Ollama, model={self.active_model}, prompt_length={len(prompt)}")
        
        try:
            # Pre-flight health check
            if not await self.health_check():
                raise Exception("Ollama service is not responding to health checks")
            
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request for vision model
            request_data = {
                "model": self.active_model or self.fallback_model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "temperature": 0.1,     # Very low temperature for consistent, controlled responses
                    "num_predict": 80,      # Strict token limit for exactly 3 sentences
                    "top_p": 0.6,          # Very focused responses
                    "repeat_penalty": 1.4,  # High penalty to reduce repetition and verbosity
                    "stop": ["4.", "4 ", "\n4", "sentence 4", "Sentence 4", "Additionally", "Furthermore", "Moreover", "Also,", "In addition", "The image also", "Overall,", "Finally,"]  # Comprehensive stops
                }
            }
            
            # Send request with health monitoring
            return await self._analyze_with_health_monitoring(request_data)
                    
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {str(e)}")
            raise
            
    async def _analyze_with_health_monitoring(self, request_data: dict) -> str:
        """
        Execute analysis with periodic health checks during long-running inference
        
        Args:
            request_data: Request payload for Ollama API
            
        Returns:
            Analysis result
        """
        # Create a separate session for health checks during inference
        health_session = aiohttp.ClientSession(timeout=self.health_timeout)
        
        # Start the inference request
        inference_task = asyncio.create_task(self._execute_inference(request_data))
        
        # Monitor health at configured intervals
        health_interval = Config.OLLAMA_HEALTH_INTERVAL
        last_health_check = asyncio.get_event_loop().time()
        
        try:
            while not inference_task.done():
                current_time = asyncio.get_event_loop().time()
                
                # Check if it's time for a health check
                if current_time - last_health_check >= health_interval:
                    logger.info("🔍 Performing health check during inference...")
                    
                    try:
                        async with health_session.get(f"{self.base_url}/api/version") as health_response:
                            if health_response.status == 200:
                                logger.info("✅ Ollama is still healthy during inference")
                            else:
                                logger.warning(f"⚠️ Ollama health check failed: {health_response.status}")
                    except Exception as e:
                        logger.warning(f"⚠️ Health check failed during inference: {e}")
                        
                    last_health_check = current_time
                
                # Wait briefly before next check
                try:
                    await asyncio.wait_for(asyncio.shield(inference_task), timeout=5)
                    break  # Task completed
                except asyncio.TimeoutError:
                    continue  # Keep monitoring
                    
            # Get the result
            result = await inference_task
            logger.info("✅ Image analysis completed successfully")
            return result
            
        finally:
            await health_session.close()
            
    async def _execute_inference(self, request_data: dict) -> str:
        """Execute the actual inference request"""
        # Use inference timeout for the actual request
        inference_session = aiohttp.ClientSession(timeout=self.inference_timeout)
        
        try:
            async with inference_session.post(self.api_url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    description = result.get('response', '').strip()
                    
                    logger.info(f"✅ Image analysis completed, description_length={len(description)}")
                    logger.info(f"📝 Generated description: {description[:100]}...")
                    
                    return description
                    
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
        finally:
            await inference_session.close()
    
    async def generate_image_description(self, image_data: bytes) -> Dict:
        """
        Generate a comprehensive image description using a single optimized prompt
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dict with description and metadata
        """
        if not self.initialized or not self.session:
            raise Exception("Ollama client not initialized")
            
        logger.info(f"🔍 Generating comprehensive image description with model: {self.active_model}")
        
        # Single comprehensive prompt for detailed German description
        comprehensive_prompt = """
Describe this image in EXACTLY 3 sentences. Use this format:
1. [Main subject and action]
2. [Setting and environment] 
3. [Key details or mood]

STOP after sentence 3. Do not write more than 3 sentences.
"""
        
        try:
            description = await self.analyze_image(image_data, comprehensive_prompt)
            
            result = {
                'description': description,
                'model_used': self.active_model,
                'analysis_type': 'comprehensive_description'
            }
            
            logger.info(f"✅ Image description completed: {description[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Image description generation failed: {str(e)}")
            raise
            

        
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            if not self.session:
                return False
                
            async with self.session.get(f"{self.base_url}/api/version") as response:
                return response.status == 200
                
        except Exception:
            return False
            
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("🔄 Ollama client session closed")