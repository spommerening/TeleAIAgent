#!/usr/bin/env python3
"""
Telegram Bot Main Entry Point (AsyncIO)
Main entry point for the Telegram Bot with AsyncIO for concurrent processing
"""

import asyncio
import logging
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from config import Config
from handlers.text_handler import TextHandler
from handlers.file_handler import FileHandler
from utils.monitoring import SystemMonitor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(Config.WORKER_LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configure HTTP libraries logging
if not Config.DEBUG_HTTP_LIBRARIES:
    # Set HTTP libraries to higher level (less spam)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('aiogram').setLevel(logging.INFO)  # Telegram Bot less verbose
    logger.info("HTTP debug logging disabled (Config.DEBUG_HTTP_LIBRARIES = False)")
else:
    logger.info("HTTP debug logging enabled (Config.DEBUG_HTTP_LIBRARIES = True)")

class AsyncTelegramBot:
    def __init__(self):
        self.bot = Bot(token=Config.BOT_TOKEN)
        self.dp = Dispatcher()
        self.text_handler = TextHandler(self.bot)
        self.file_handler = FileHandler(self.bot)
        self.monitor = SystemMonitor()
        self._setup_handlers()
        self._setup_signal_handlers()
        
    def _setup_handlers(self):
        """Sets up message handlers"""
        logger.info("Setting up async message handlers...")
        
        # Command handlers
        @self.dp.message(Command("start"))
        async def handle_start_command(message: Message):
            try:
                welcome_text = f"""
🤖 Welcome to TeleAI Agent! 

I'm your AI-powered assistant that can:
• Answer questions using AI
• Process and download files (images, documents, voice, video)
• Maintain conversation context
• Work in both private chats and groups

In groups, mention me with @{(await self.bot.me()).username} or reply to my messages.
In private chats, just send me your message!

Ask me anything! 🚀
                """.strip()
                await message.answer(welcome_text)
                logger.info(f"Start command handled for user {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error in start command handler: {e}", exc_info=True)

        @self.dp.message(Command("help"))
        async def handle_help_command(message: Message):
            try:
                help_text = f"""
🔧 TeleAI Agent Help

**Commands:**
• /start - Show welcome message
• /help - Show this help message
• /status - Show bot status

**Features:**
• 💬 AI-powered conversations
• 📁 File processing (images, documents, voice, video)
• 🧠 Context-aware responses
• 🔍 Semantic search in conversation history

**Usage:**
• In groups: mention @{(await self.bot.me()).username} or reply to my messages
• In private: just send your message
• Send files and I'll process them automatically

Need more help? Just ask me! 🤝
                """.strip()
                await message.answer(help_text)
                logger.info(f"Help command handled for user {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error in help command handler: {e}", exc_info=True)

        @self.dp.message(Command("status"))
        async def handle_status_command(message: Message):
            try:
                status_text = f"""
📊 Bot Status

✅ Bot is running
🔧 Backend: {Config.AI_BACKEND}
🏃‍♂️ AsyncIO: Enabled (Concurrent Processing)
💾 Context: {'ChromaDB' if hasattr(self.text_handler.context_manager, 'is_chromadb_available') and self.text_handler.context_manager.is_chromadb_available() else 'File-based'}

System is operational! 🚀
                """.strip()
                await message.answer(status_text)
                logger.info(f"Status command handled for user {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error in status command handler: {e}", exc_info=True)

        # Photo handlers
        @self.dp.message(lambda message: message.photo)
        async def handle_photos(message: Message):
            try:
                await self.file_handler.handle_message(message)
                await self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing photo: {e}", exc_info=True)
                
        # Document handlers
        @self.dp.message(lambda message: message.document)
        async def handle_documents(message: Message):
            try:
                await self.file_handler.handle_message(message)
                await self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing document: {e}", exc_info=True)
                
        # Voice handlers
        @self.dp.message(lambda message: message.voice)
        async def handle_voice(message: Message):
            try:
                await self.file_handler.handle_message(message)
                await self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing voice: {e}", exc_info=True)
                
        # Video and audio handlers
        @self.dp.message(lambda message: message.video or message.audio)
        async def handle_media(message: Message):
            try:
                await self.file_handler.handle_message(message)
                await self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing media: {e}", exc_info=True)

        # Text message handlers
        @self.dp.message(lambda message: message.text and not message.text.startswith('/'))
        async def handle_text_messages(message: Message):
            try:
                # Only process text messages that are not commands
                await self.text_handler.handle_message(message)
            except Exception as e:
                logger.error(f"Error processing text message: {e}", exc_info=True)
                
    def _setup_signal_handlers(self):
        """Sets up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Signal {signum} received, shutting down bot...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def start_polling(self):
        """Starts bot polling"""
        logger.info(f"AsyncIO Bot started. Waiting for messages...")
        
        # Initialize AI client
        await self.text_handler.ai_client.initialize()
        
        # Initialize file handler (for tagger client)
        await self.file_handler.initialize()
        
        # Start monitoring
        await self.monitor.start_monitoring()
        
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            raise
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shuts down the bot"""
        logger.info("Bot shutting down...")
        await self.monitor.stop_monitoring()
        
        # Close tagger client connection
        if hasattr(self.file_handler, 'tagger_client'):
            await self.file_handler.tagger_client.close()
            
        await self.bot.session.close()
        logger.info("Bot successfully shut down")

async def main():
    """Main async function"""
    try:
        bot = AsyncTelegramBot()
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())