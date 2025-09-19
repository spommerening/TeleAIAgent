"""
Ollama Client for Image Analysis
Handles communication with Ollama service for image tagging
"""

import asyncio
import base64
import json
import logging
from typing import List, Optional

import aiohttp

from config import Config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama for image analysis"""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_URL
        self.api_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self.model = Config.OLLAMA_MODEL
        self.session: Optional[aiohttp.ClientSession] = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the Ollama client and ensure model is available"""
        logger.info(f"🔧 Initializing Ollama client, model={self.model}, url={self.base_url}")
        
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
        """Ensure the required model is available, pull if necessary"""
        logger.info(f"🔍 Checking model availability, model={self.model}")
        
        try:
            # List available models
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    available_models = [model['name'] for model in models_data.get('models', [])]
                    
                    if self.model in available_models:
                        logger.info(f"✅ Model already available, model={self.model}")
                        return
                    
            # Model not available, pull it
            logger.info(f"📥 Pulling model from Ollama registry, model={self.model}")
            
            pull_data = {"name": self.model}
            async with self.session.post(f"{self.base_url}/api/pull", json=pull_data) as response:
                if response.status == 200:
                    # Stream the download progress
                    async for line in response.content:
                        if line:
                            try:
                                progress_data = json.loads(line)
                                status = progress_data.get('status', '')
                                if 'pulling' in status.lower():
                                    logger.info(f"📥 Download progress, status={status}")
                                elif status == 'success':
                                    logger.info(f"✅ Model downloaded successfully, model={self.model}")
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    raise Exception(f"Failed to pull model: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to ensure model availability: {str(e)}")
            raise
            
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
            
        logger.info(f"🔍 Analyzing image with Ollama, model={self.model}, prompt_length={len(prompt)}")
        
        try:
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request for vision model
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "temperature": Config.OLLAMA_TEMPERATURE,
                    "num_predict": 100  # Limit response length for tags
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