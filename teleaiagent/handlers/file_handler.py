"""
File Message Handler (AsyncIO)
Handler for files, images, videos etc.
"""

import logging
import aiohttp
import aiofiles
import os
import time
import io
from PIL import Image
from config import Config
from utils.tagger_client import TaggerClient

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, bot):
        self.bot = bot
        self.bot_token = Config.BOT_TOKEN
        self.tagger_client = TaggerClient()
        
    async def initialize(self):
        """Initialize tagger client and check service health"""
        await self.tagger_client.initialize()
        
        # Check if tagger service is available
        is_healthy = await self.tagger_client.health_check()
        if is_healthy:
            logger.info("✅ Tagger service is healthy and ready")
        else:
            logger.warning("⚠️ Tagger service is not responding - images will be processed without tagging")
        
    async def handle_message(self, message):
        """Processes incoming files"""
        
        if message.photo:
            await self._download_photos(message)
        elif message.document:
            await self._download_documents(message)
        elif message.voice:
            await self._download_voice(message)
        elif message.video or message.audio:
            await self._download_media(message)
    
    async def _download_photos(self, message):
        """Process photos by forwarding to tagger service"""
        
        # Find largest photo
        largest_photo = max(message.photo, key=lambda x: (x.width, x.height))
        photo_id = largest_photo.file_id
        
        try:
            # Get file info and download image data
            file_info = await self.bot.get_file(photo_id)
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            
            # Download image data
            raw_image_data = await self._download_image_data(download_url)
            
            # Convert image to JPEG format
            jpg_image_data = self._convert_to_jpeg(raw_image_data)
            
            # Prepare Telegram metadata
            telegram_metadata = self._extract_telegram_metadata(message, file_info, photo_id)
            
            # Check if tagger service is healthy before processing
            is_healthy = await self.tagger_client.health_check()
            if not is_healthy:
                logger.warning("⚠️ Tagger service is not healthy, skipping tagging for this image")
                return
            
            # Send to tagger service for processing
            result = await self.tagger_client.process_image(
                image_data=jpg_image_data,
                telegram_metadata=telegram_metadata,
                filename=f"{photo_id}.jpg"
            )
            
            if result:
                logger.info(f"✅ Photo processed by tagger service: {result.get('result', {}).get('tags', [])}")
            else:
                logger.warning("⚠️ Tagger service failed to process image, continuing without tagging")
            
        except Exception as e:
            logger.error(f"❌ Error processing photo with tagger service: {e}", exc_info=True)
    
    async def _download_documents(self, message):
        """Downloads documents"""
        logger.info(f"Document message: {message.document}")
        
        document = message.document
        document_id = document.file_id
        file_info = await self.bot.get_file(document_id)
        
        # Determine file extension
        file_extension = document.mime_type.split('/')[-1] if document.mime_type else 'bin'
        file_path = os.path.join(Config.DOCUMENTS_DIR, f"{document_id}.{file_extension}")
        
        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
        await self._download_file(download_url, file_path)
    
    async def _download_voice(self, message):
        """Downloads voice messages"""
        logger.info(f"Voice message: {message.voice}")
        
        voice_id = message.voice.file_id
        file_info = await self.bot.get_file(voice_id)
        
        file_path = os.path.join(Config.VOICE_DIR, f"{voice_id}.ogg")
        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
        
        await self._download_file(download_url, file_path)
    
    async def _download_media(self, message):
        """Downloads videos and audio"""
        if message.video:
            logger.info(f"Video message: {message.video}")
            video_id = message.video.file_id
            file_info = await self.bot.get_file(video_id)
            file_path = os.path.join(Config.VIDEOS_DIR, f"{video_id}.mp4")
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            await self._download_file(download_url, file_path)
            
        if message.audio:
            logger.info(f"Audio message: {message.audio}")
            audio_id = message.audio.file_id
            file_info = await self.bot.get_file(audio_id)
            file_path = os.path.join(Config.AUDIO_DIR, f"{audio_id}.mp3")
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            await self._download_file(download_url, file_path)
    
    async def _download_image_data(self, download_url):
        """Download image data and return bytes (for tagger service)"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Download failed. Status: {response.status}")
                        raise Exception(f"Download failed with status: {response.status}")
            except Exception as e:
                logger.error(f"Download error: {e}")
                raise

    def _convert_to_jpeg(self, image_data):
        """Convert image to JPEG format regardless of input format"""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Get original format for logging
            original_format = image.format or "Unknown"
            logger.info(f"🔄 Converting image from {original_format} to JPEG")
            
            # Convert RGBA to RGB if necessary (for PNG with transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save as JPEG
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=95, optimize=True)
            jpeg_data = output_buffer.getvalue()
            
            logger.info(f"✅ Image converted to JPEG - original: {len(image_data)} bytes, converted: {len(jpeg_data)} bytes")
            return jpeg_data
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to convert image to JPEG, using original: {e}")
            return image_data

    def _extract_telegram_metadata(self, message, file_info, file_id):
        """Extract Telegram message metadata for tagger service"""
        # Handle aiogram datetime object
        if hasattr(message.date, 'strftime'):  # It's already a datetime object
            timestamp_str = message.date.strftime('%Y-%m-%d %H:%M:%S')
        else:  # Fallback for Unix timestamp
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message.date))
        
        return {
            'chat_id': message.chat.id,
            'chat_title': message.chat.title if message.chat.title else message.chat.first_name,
            'chat_type': message.chat.type,
            'user_id': message.from_user.id,
            'user_name': message.from_user.first_name,
            'message_id': message.message_id,
            'timestamp': timestamp_str,
            'date': time.strftime('%Y-%m-%d', time.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')),
            'file_id': file_id,
            'file_size': file_info.file_size,
            'has_caption': bool(message.caption),
            'caption': message.caption or ""
        }

    async def _download_file(self, download_url, file_path):
        """Universal file download function (for non-image files)"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(content)
                    else:
                        logger.error(f"Download failed. Status: {response.status}")
            except Exception as e:
                logger.error(f"Download error: {e}")
