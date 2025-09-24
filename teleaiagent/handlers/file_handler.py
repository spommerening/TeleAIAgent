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
import asyncio
from collections import deque
from PIL import Image
from config import Config
from utils.vision_client import VisionClient

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, bot):
        self.bot = bot
        self.bot_token = Config.BOT_TOKEN
        self.vision_client = VisionClient()

        # Global image processing queue (FIFO)
        self._image_queue = asyncio.Queue()
        self._queue_processor = None
        self._processing_stats = {
            'total_processed': 0,
            'currently_processing': False,
            'queue_size': 0
        }
        
    async def initialize(self):
        """Initialize vision client and start global queue processor"""
        await self.vision_client.initialize()

        # Check if vision service is available
        is_healthy = await self.vision_client.health_check()
        if is_healthy:
            logger.info("✅ Vision service is healthy and ready")
        else:
            logger.warning("⚠️ Vision service is not responding - images will be processed without tagging")

        # Start global queue processor
        self._queue_processor = asyncio.create_task(self._process_image_queue())
        logger.info("🔄 Global image processing queue started")
        
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
        """Queue photo for global processing to prevent Ollama overload"""
        
        # Find largest photo
        largest_photo = max(message.photo, key=lambda x: (x.width, x.height))
        photo_id = largest_photo.file_id
        
        try:
            # Quick health check before queuing
            is_healthy = await self.vision_client.health_check()
            if not is_healthy:
                logger.warning("⚠️ Vision service is not healthy, rejecting image")
                await message.reply("❌ Bildverarbeitungsservice ist derzeit nicht verfügbar. Bitte versuche es später noch einmal.")
                return
            
            # Get file info and download image data immediately
            file_info = await self.bot.get_file(photo_id)
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_info.file_path}"
            
            # Download and prepare image data
            raw_image_data = await self._download_image_data(download_url)
            jpg_image_data = self._convert_to_jpeg(raw_image_data)
            
            # Prepare Telegram metadata
            telegram_metadata = self._extract_telegram_metadata(message, file_info, photo_id)
            
            # Create processing task
            processing_task = {
                'message': message,
                'image_data': jpg_image_data,
                'metadata': telegram_metadata,
                'filename': f"{photo_id}.jpg",
                'queued_at': time.time(),
                'user_id': message.from_user.id,
                'chat_id': message.chat.id
            }
            
            # Add to global queue
            await self._image_queue.put(processing_task)
            self._processing_stats['queue_size'] = self._image_queue.qsize()
            
            # Send immediate acknowledgment with queue position
            queue_position = self._image_queue.qsize()
            if queue_position == 1 and not self._processing_stats['currently_processing']:
                await message.reply("📥 Bild empfangen! Verarbeitung startet sofort...")
            else:
                estimated_wait = (queue_position - 1) * 3  # Estimate 3 minutes per image
                await message.reply(f"📥 Bild empfangen! Position in Warteschlange: {queue_position}\n⏱️ Geschätzte Wartezeit: ~{estimated_wait} Minuten")
            
            logger.info(f"🔄 Image queued for processing, user={message.from_user.id}, queue_size={queue_position}")
            
        except Exception as e:
            logger.error(f"❌ Error queuing photo: {e}", exc_info=True)
            try:
                await message.reply("❌ Fehler beim Empfangen des Bildes. Bitte versuche es noch einmal.")
            except:
                pass

    async def _process_image_queue(self):
        """Global queue processor - processes one image at a time"""
        logger.info("🔄 Global image queue processor started")
        
        while True:
            try:
                # Wait for next image to process
                task = await self._image_queue.get()
                
                # Update processing stats
                self._processing_stats['currently_processing'] = True
                self._processing_stats['queue_size'] = self._image_queue.qsize()
                
                logger.info(f"🤖 Processing image for user {task['user_id']}, queue remaining: {self._processing_stats['queue_size']}")
                
                # Process the image
                await self._process_single_image_task(task)
                
                # Update stats
                self._processing_stats['total_processed'] += 1
                self._processing_stats['currently_processing'] = False
                self._image_queue.task_done()
                
                logger.info(f"✅ Image processing completed, total processed: {self._processing_stats['total_processed']}")
                
            except Exception as e:
                logger.error(f"❌ Error in image queue processor: {e}", exc_info=True)
                self._processing_stats['currently_processing'] = False
                
    async def _process_single_image_task(self, task):
        """Process a single queued image task"""
        message = task['message']
        image_data = task['image_data']
        metadata = task['metadata']
        filename = task['filename']
        
        processing_msg = None
        
        try:
            # Send processing notification
            queue_wait = time.time() - task['queued_at']
            processing_msg = await message.reply(f"🤖 Analysiere Bild...\n⏱️ Wartezeit: {queue_wait:.0f}s")
            
            # Send to vision service for processing
            result = await self.vision_client.process_image(
                image_data=image_data,
                telegram_metadata=metadata,
                filename=filename
            )
            
            if result and result.get('status') == 'success':
                # Extract description from result
                description = result.get('result', {}).get('description', 'Keine Beschreibung verfügbar')
                quality_score = result.get('result', {}).get('quality_score', 0)
                
                # Calculate total processing time
                total_time = time.time() - task['queued_at']
                
                # Format reply message with description
                reply_text = f"📸 **Bildanalyse:**\n\n{description}"
                
                # Add quality and timing info
                if quality_score > 0:
                    quality_emoji = "🟢" if quality_score > 0.7 else "🟡" if quality_score > 0.4 else "🔴"
                    reply_text += f"\n\n{quality_emoji} Qualität: {quality_score:.1%}"
                
                reply_text += f"\n⏱️ Gesamtzeit: {total_time:.0f}s"
                
                # Edit the processing message with the final result
                await self.bot.edit_message_text(
                    chat_id=processing_msg.chat.id,
                    message_id=processing_msg.message_id,
                    text=reply_text,
                    parse_mode="Markdown"
                )
                
                logger.info(f"✅ Photo processed and replied with description: {description[:50]}...")
            else:
                # Handle failure
                await self.bot.edit_message_text(
                    chat_id=processing_msg.chat.id,
                    message_id=processing_msg.message_id,
                    text="❌ Bildverarbeitung fehlgeschlagen. Bitte versuche es noch einmal."
                )
                logger.warning("⚠️ Vision service failed to process image")
            
        except Exception as e:
            logger.error(f"❌ Error processing single image task: {e}", exc_info=True)
            # Try to send error message to user
            try:
                if processing_msg:
                    await self.bot.edit_message_text(
                        chat_id=processing_msg.chat.id,
                        message_id=processing_msg.message_id,
                        text="❌ Fehler bei der Bildverarbeitung aufgetreten."
                    )
                else:
                    await message.reply("❌ Fehler bei der Bildverarbeitung aufgetreten.")
            except Exception:
                pass

    def get_queue_stats(self):
        """Get current queue statistics"""
        return {
            'queue_size': self._image_queue.qsize(),
            'currently_processing': self._processing_stats['currently_processing'],
            'total_processed': self._processing_stats['total_processed']
        }
    
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
        """Download image data and return bytes (for vision service)"""
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
        """Extract Telegram message metadata for vision service"""
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
