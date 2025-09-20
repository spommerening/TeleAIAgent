"""
Ollama Client for Image Analysis
Handles communication with Ollama service for image tagging
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
        self.primary_model = getattr(Config, 'PRIMARY_VISION_MODEL', Config.OLLAMA_MODEL)
        self.fallback_model = getattr(Config, 'FALLBACK_VISION_MODEL', 'llava:7b')
        self.active_model = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the Ollama client and ensure model is available"""
        logger.info(f"🔧 Initializing Ollama client, primary_model={self.primary_model}, fallback_model={self.fallback_model}, url={self.base_url}")
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for model downloads
        self.session = aiohttp.ClientSession(timeout=timeout)
        
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
        """Ensure the best available model is ready, with fallback support"""
        logger.info(f"🔍 Checking model availability, primary={self.primary_model}, fallback={self.fallback_model}")
        
        try:
            # List available models
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    available_models = [model['name'] for model in models_data.get('models', [])]
                    
                    # Try primary model first
                    if self.primary_model in available_models:
                        self.active_model = self.primary_model
                        logger.info(f"✅ Using primary vision model: {self.active_model}")
                        return
                    
                    # Check if fallback is available
                    if self.fallback_model in available_models:
                        self.active_model = self.fallback_model
                        logger.info(f"⚠️ Primary model not available, using fallback: {self.active_model}")
                        return
                    
            # Try to pull primary model
            logger.info(f"📥 Primary model not found, attempting to pull: {self.primary_model}")
            
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
        Analyze image and generate a comprehensive description using Ollama
        
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
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request for vision model
            request_data = {
                "model": self.active_model or self.fallback_model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "temperature": 0.7,     # Balanced creativity for descriptions
                    "num_predict": 300,     # Allow longer descriptions
                    "top_p": 0.9,          # Slightly more focused responses
                    "repeat_penalty": 1.1   # Reduce repetition
                }
            }
            
            # Send request to Ollama
            async with self.session.post(self.api_url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    description = result.get('response', '').strip()
                    
                    logger.info(f"✅ Image analysis completed, description_length={len(description)}")
                    logger.info(f"📝 Generated description: {description[:100]}...")
                    
                    return description
                    
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {str(e)}")
            raise
    
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
        comprehensive_prompt = """Analysiere dieses Bild und gib eine detaillierte Beschreibung auf Deutsch, die folgende Aspekte umfasst:
- Welche Objekte, Personen oder Motive sind sichtbar
- Die Umgebung, der Ort oder die Atmosphäre
- Farben, Beleuchtung und visueller Stil
- Stimmung, Atmosphäre oder emotionaler Ton
- Bemerkenswerte Aktivitäten oder Interaktionen
- Technische Aspekte wie Komposition oder Perspektive

Gib eine umfassende, natürliche Beschreibung in 2-4 Sätzen auf Deutsch, die das Wesen des Bildes einfängt."""
        
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