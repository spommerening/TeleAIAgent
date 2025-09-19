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
        self.primary_model = getattr(Config, 'PRIMARY_VISION_MODEL', 'llava:7b')
        self.fallback_model = getattr(Config, 'FALLBACK_VISION_MODEL', Config.OLLAMA_MODEL)
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
            
    async def analyze_image(self, image_data: bytes, prompt: Optional[str] = None) -> List[str]:
        """
        Analyze image and generate tags using Ollama
        
        Args:
            image_data: Raw image bytes
            prompt: Optional custom prompt (uses default if not provided)
            
        Returns:
            List of generated tags
        """
        if not self.initialized or not self.session:
            raise Exception("Ollama client not initialized")
            
        # Use default prompt if none provided
        if prompt is None:
            prompt = Config.IMAGE_TAGGING_PROMPT
            
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
                    "temperature": Config.OLLAMA_TEMPERATURE,
                    "num_predict": 200,  # Increased for more detailed tags
                    "top_p": 0.9,       # Slightly more focused responses
                    "repeat_penalty": 1.1  # Reduce repetition
                }
            }
            
            # Send request to Ollama
            async with self.session.post(self.api_url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get('response', '').strip()
                    
                    logger.info(f"✅ Image analysis completed, response_length={len(response_text)}")
                    
                    # Parse tags from response
                    tags = self._parse_tags(response_text)
                    
                    logger.info(f"🏷️ Generated tags, tags={tags}, count={len(tags)}")
                    return tags
                    
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {str(e)}")
            raise
    
    async def analyze_image_multi_pass(self, image_data: bytes) -> Dict:
        """
        Perform multi-pass image analysis with different prompts
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dict with results from different analysis passes
        """
        if not self.initialized or not self.session:
            raise Exception("Ollama client not initialized")
            
        logger.info(f"🔍 Starting multi-pass image analysis with model: {self.active_model}")
        
        try:
            # Primary detailed analysis
            primary_tags = await self.analyze_image(image_data, Config.IMAGE_TAGGING_PROMPT)
            
            # Artistic analysis
            artistic_tags = await self.analyze_image(image_data, Config.ARTISTIC_ANALYSIS_PROMPT)
            
            # Contextual analysis  
            contextual_tags = await self.analyze_image(image_data, Config.CONTEXTUAL_ANALYSIS_PROMPT)
            
            result = {
                'primary_tags': primary_tags,
                'artistic_tags': artistic_tags,
                'contextual_tags': contextual_tags,
                'model_used': self.active_model,
                'total_passes': 3
            }
            
            logger.info(f"✅ Multi-pass analysis completed: {len(primary_tags)} + {len(artistic_tags)} + {len(contextual_tags)} tags")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Multi-pass image analysis failed: {str(e)}")
            # Fallback to single pass
            logger.info("🔄 Falling back to single-pass analysis")
            primary_tags = await self.analyze_image(image_data, Config.IMAGE_TAGGING_PROMPT)
            return {
                'primary_tags': primary_tags,
                'artistic_tags': [],
                'contextual_tags': [],
                'model_used': self.active_model,
                'total_passes': 1,
                'fallback_mode': True
            }
            
    def _parse_tags(self, response_text: str) -> List[str]:
        """
        Parse tags from Ollama response text
        
        Args:
            response_text: Raw response from Ollama
            
        Returns:
            List of parsed tags
        """
        # Clean and split response into tags
        tags = []
        
        # Remove common prefixes/suffixes
        text = response_text.lower().strip()
        
        # Remove common response patterns
        patterns_to_remove = [
            "tags:", "the tags are:", "i can see:", "the image shows:",
            "tags for this image:", "description:", "here are the tags:"
        ]
        
        for pattern in patterns_to_remove:
            if text.startswith(pattern):
                text = text[len(pattern):].strip()
                break
        
        # Split by common separators
        if ',' in text:
            # Comma-separated
            raw_tags = text.split(',')
        elif ';' in text:
            # Semicolon-separated
            raw_tags = text.split(';')
        elif '\n' in text:
            # Line-separated
            raw_tags = text.split('\n')
        else:
            # Space-separated (fallback)
            raw_tags = text.split()
            
        # Clean each tag
        for tag in raw_tags:
            cleaned_tag = tag.strip().strip('.,;:"\'()[]{}')
            if cleaned_tag and len(cleaned_tag) > 1:
                tags.append(cleaned_tag)
                
        # Limit number of tags
        return tags[:10]  # Max 10 tags
        
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