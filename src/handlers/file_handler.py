"""
File Message Handler
Handler for files, images, videos etc.
"""

import logging
import requests
import os
from config import Config

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, bot):
        self.bot = bot
        self.bot_token = Config.BOT_TOKEN
        
    def handle_message(self, message):
        """Processes incoming files"""
        logger.info(f"FileHandler called - Chat type: {message.chat.type}, Content type: {message.content_type}")
        logger.info(f"FileHandler - Photo: {bool(message.photo)}, Document: {bool(message.document)}, Voice: {bool(message.voice)}, Video: {bool(message.video)}, Audio: {bool(message.audio)}")
        
        if message.photo:
            logger.info("FileHandler: Processing photo...")
            self._download_photos(message)
        elif message.document:
            logger.info("FileHandler: Processing document...")
            self._download_documents(message)
        elif message.voice:
            logger.info("FileHandler: Processing voice...")
            self._download_voice_messages(message)
        elif message.video or message.audio:
            logger.info("FileHandler: Processing video/audio...")
            self._download_other_files(message)
        else:
            logger.info("FileHandler: No media files detected in this message")
    
    def _download_photos(self, message):
        """Downloads photos"""
        logger.info(f"Downloading photo - Chat type: {message.chat.type}, Photo count: {len(message.photo)}")
        
        # Find largest photo
        largest_photo = max(message.photo, key=lambda x: (x.width, x.height))
        
        photo_id = largest_photo.file_id
        logger.info(f"Photo ID: {photo_id}")
        
        try:
            file_info = self.bot.get_file(photo_id)
            file_path = os.path.join(Config.IMAGES_DIR, f"{photo_id}.jpg")
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            
            logger.info(f"Downloading to: {file_path}")
            self._download_file(download_url, file_path)
            logger.info(f"Photo download completed: {file_path}")
        except Exception as e:
            logger.error(f"Error downloading photo: {e}", exc_info=True)
    
    def _download_documents(self, message):
        """Downloads documents"""
        logger.info(f"Document message: {message.document}")
        
        document = message.document
        document_id = document.file_id
        file_info = self.bot.get_file(document_id)
        
        # Determine file extension
        file_extension = document.mime_type.split('/')[-1] if document.mime_type else 'bin'
        file_path = os.path.join(Config.DOCUMENTS_DIR, f"{document_id}.{file_extension}")
        
        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
        self._download_file(download_url, file_path)
    
    def _download_voice_messages(self, message):
        """Downloads voice messages"""
        logger.info(f"Voice message: {message.voice}")
        
        voice_id = message.voice.file_id
        file_info = self.bot.get_file(voice_id)
        
        file_path = os.path.join(Config.VOICE_DIR, f"{voice_id}.ogg")
        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
        
        self._download_file(download_url, file_path)
    
    def _download_other_files(self, message):
        """Downloads videos and audio"""
        if message.video:
            logger.info(f"Video message: {message.video}")
            video_id = message.video.file_id
            file_info = self.bot.get_file(video_id)
            file_path = os.path.join(Config.VIDEOS_DIR, f"{video_id}.mp4")
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            self._download_file(download_url, file_path)
            
        if message.audio:
            logger.info(f"Audio message: {message.audio}")
            audio_id = message.audio.file_id
            file_info = self.bot.get_file(audio_id)
            file_path = os.path.join(Config.AUDIO_DIR, f"{audio_id}.mp3")
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            self._download_file(download_url, file_path)
    
    def _download_file(self, download_url, file_path):
        """Universal file download function"""
        try:
            response = requests.get(download_url)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"File saved: {file_path}")
            else:
                logger.error(f"Download failed. Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Download error: {e}")
