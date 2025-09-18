"""
File Message Handler (AsyncIO)
Handler for files, images, videos etc.
"""

import logging
import aiohttp
import aiofiles
import os
from config import Config

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, bot):
        self.bot = bot
        self.bot_token = Config.BOT_TOKEN
        
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
        """Downloads photos"""
        
        # Find largest photo
        largest_photo = max(message.photo, key=lambda x: (x.width, x.height))
        
        photo_id = largest_photo.file_id
        
        try:
            file_info = await self.bot.get_file(photo_id)
            file_path = os.path.join(Config.IMAGES_DIR, f"{photo_id}.jpg")
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            
            await self._download_file(download_url, file_path)
        except Exception as e:
            logger.error(f"Error downloading photo: {e}", exc_info=True)
    
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
    
    async def _download_file(self, download_url, file_path):
        """Universal file download function"""
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
