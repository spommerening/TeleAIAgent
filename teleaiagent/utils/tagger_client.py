"""
Tagger Client for TeleAI Agent
Client to communicate with the tagger microservice
"""

import asyncio
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
        # Long timeout for AI image processing: up to 10 minutes total
        timeout = aiohttp.ClientTimeout(
            total=660,  # 11 minutes total (10 min processing + 1 min buffer)
            connect=30,  # Connection timeout (keep short for quick failure detection)
            sock_read=None  # No socket read timeout for long-running AI operations
        )
        connector = aiohttp.TCPConnector(
            limit=5,  # Smaller connection pool for long-running operations
            limit_per_host=2,  # Max connections per host (reduced for long operations)
            keepalive_timeout=60,  # Longer keep alive for sustained connections
            enable_cleanup_closed=True  # Clean up closed connections
        )
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': 'TeleAI-Agent/1.0'}
        )
        logger.info(f"🔧 Tagger client initialized, url={self.tagger_url} (timeout: 11 minutes for AI processing)")
        
    async def process_image(
        self,
        image_data: bytes,
        telegram_metadata: Dict,
        filename: str = "image.jpg",
        max_retries: int = 1
    ) -> Optional[Dict]:
        """
        Send image to tagger service for processing with retry logic
        Designed for long-running AI operations (up to 10 minutes per attempt)
        
        Args:
            image_data: Raw image bytes
            telegram_metadata: Metadata from Telegram message
            filename: Original filename
            max_retries: Maximum number of retry attempts (default: 1 for 10-min operations)
            
        Returns:
            Response from tagger service or None if all retries failed
        """
        if not self.session:
            logger.error("❌ Tagger client not initialized")
            return None
            
        logger.info(f"📤 Sending image to tagger service, filename={filename}, size_bytes={len(image_data)}, chat_id={telegram_metadata.get('chat_id')}")
        
        for attempt in range(max_retries + 1):
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
                        
                        # Don't retry on client errors (4xx), only server errors (5xx) and timeouts
                        if 400 <= response.status < 500:
                            logger.error(f"❌ Client error {response.status}, not retrying")
                            return None
                        
                        if attempt < max_retries:
                            wait_time = 60  # Fixed 1-minute wait for long-running AI operations
                            logger.warning(f"⏳ Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1}) - AI processing can take up to 10 minutes")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"❌ All retry attempts failed for tagger service")
                            return None
                            
            except asyncio.TimeoutError:
                logger.error(f"⏱️ Timeout error after 11 minutes on attempt {attempt + 1}/{max_retries + 1}")
                if attempt < max_retries:
                    wait_time = 120  # 2-minute wait after timeout for AI processing
                    logger.warning(f"⏳ Retrying after timeout in {wait_time}s - AI processing may need more time")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ All retry attempts failed due to timeout (AI processing took longer than 11 minutes)")
                    return None
                    
            except asyncio.CancelledError:
                logger.error(f"🚫 Request cancelled on attempt {attempt + 1}")
                # Don't retry on cancellation
                return None
                
            except aiohttp.ClientError as e:
                logger.error(f"🌐 Client error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    wait_time = 60  # 1-minute wait for client errors
                    logger.warning(f"⏳ Retrying after client error in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ All retry attempts failed due to client errors")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    wait_time = 60  # 1-minute wait for unexpected errors
                    logger.warning(f"⏳ Retrying after error in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ All retry attempts failed due to unexpected errors")
                    return None
        
        return None
            
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
            logger.error("❌ Tagger client not initialized")
            return []
            
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
                    
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout while searching similar images")
            return []
        except asyncio.CancelledError:
            logger.error(f"🚫 Search similar images request cancelled")
            return []
        except aiohttp.ClientError as e:
            logger.error(f"🌐 Client error while searching similar images: {str(e)}")
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
                    
        except asyncio.TimeoutError:
            return {"error": "timeout"}
        except asyncio.CancelledError:
            return {"error": "cancelled"}
        except aiohttp.ClientError as e:
            return {"error": f"client_error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
            
    async def health_check(self) -> bool:
        """Check if tagger service is healthy"""
        if not self.session:
            return False
            
        try:
            # Use a reasonable timeout for health checks (30s to account for model loading)
            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.get(f"{self.tagger_url}/health", timeout=timeout) as response:
                return response.status == 200
        except (asyncio.TimeoutError, asyncio.CancelledError, aiohttp.ClientError, Exception):
            return False
            
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("🔄 Tagger client session closed")