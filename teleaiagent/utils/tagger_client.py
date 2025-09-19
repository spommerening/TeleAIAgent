"""
Tagger Client for TeleAI Agent
Client to communicate with the tagger microservice
"""

import json
import logging
from typing import Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class TaggerClient:
    """Client for communicating with the tagger microservice"""
    
    def __init__(self, tagger_url: str = "http://tagger:7777"):
        self.tagger_url = tagger_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize the HTTP session"""
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for image processing
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info(f"🔧 Tagger client initialized, url={self.tagger_url}")
        
    async def process_image(
        self,
        image_data: bytes,
        telegram_metadata: Dict,
        filename: str = "image.jpg"
    ) -> Dict:
        """
        Send image to tagger service for processing
        
        Args:
            image_data: Raw image bytes
            telegram_metadata: Metadata from Telegram message
            filename: Original filename
            
        Returns:
            Response from tagger service
        """
        if not self.session:
            raise Exception("Tagger client not initialized")
            
        logger.info(f"📤 Sending image to tagger service, filename={filename}, size_bytes={len(image_data)}, chat_id={telegram_metadata.get('chat_id')}")
        
        try:
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('image', 
                          image_data, 
                          filename=filename,
                          content_type='image/jpeg')
            data.add_field('telegram_metadata', json.dumps(telegram_metadata))
            
            # Send request to tagger service
            async with self.session.post(f"{self.tagger_url}/tag-image", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Image processed by tagger service - tags: {result.get('result', {}).get('tags', [])}, document_id: {result.get('result', {}).get('document_id')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Tagger service error - status: {response.status}, error: {error_text}")
                    raise Exception(f"Tagger service error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to process image with tagger service: {str(e)}")
            raise
            
    async def search_similar_images(
        self,
        tags: List[str],
        chat_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for similar images using tagger service
        
        Args:
            tags: Tags to search for
            chat_id: Optional chat ID filter
            limit: Maximum results
            
        Returns:
            List of similar images
        """
        if not self.session:
            raise Exception("Tagger client not initialized")
            
        try:
            params = {
                'tags': ','.join(tags),
                'limit': limit
            }
            if chat_id:
                params['chat_id'] = chat_id
                
            async with self.session.get(f"{self.tagger_url}/search-similar", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Similar images search failed, status={response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to search similar images: {str(e)}")
            return []
            
    async def get_tagger_stats(self) -> Dict:
        """Get statistics from tagger service"""
        if not self.session:
            return {"error": "not_initialized"}
            
        try:
            async with self.session.get(f"{self.tagger_url}/stats") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
                    
        except Exception as e:
            return {"error": str(e)}
            
    async def health_check(self) -> bool:
        """Check if tagger service is healthy"""
        if not self.session:
            return False
            
        try:
            async with self.session.get(f"{self.tagger_url}/health") as response:
                return response.status == 200
        except Exception:
            return False
            
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("🔄 Tagger client session closed")