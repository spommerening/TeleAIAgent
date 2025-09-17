#!/usr/bin/env python3
"""
Telegram Bot Main Entry Point
Main entry point for the Telegram Bot with extended functionality
"""

import telebot
import logging
import signal
import sys
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
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('telebot').setLevel(logging.INFO)  # Telegram Bot less verbose
    logger.info("HTTP debug logging disabled (Config.DEBUG_HTTP_LIBRARIES = False)")
else:
    logger.info("HTTP debug logging enabled (Config.DEBUG_HTTP_LIBRARIES = True)")

class TelegramBot:
    def __init__(self):
        self.bot = telebot.TeleBot(Config.BOT_TOKEN)
        self.text_handler = TextHandler(self.bot)
        self.file_handler = FileHandler(self.bot)
        self.monitor = SystemMonitor()
        self._setup_handlers()
        self._setup_signal_handlers()
        
    def _setup_handlers(self):
        """Registers all message handlers"""
        # First register the specific command handlers
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = f"""
            Welcome! I am your AI assistant.
            
            Available commands:
            /start - Shows this welcome message
            /help - Shows this help
            /stats - Shows system and context statistics
            /reconnect - Attempts ChromaDB reconnection
            
            Just send me a message and I'll be happy to respond!
            """
            self.bot.reply_to(message, welcome_text.strip())
            
        # Reconnect ChromaDB Command Handler
        @self.bot.message_handler(commands=['reconnect'])
        def reconnect_chromadb(message):
            try:
                self.bot.reply_to(message, "🔄 Attempting ChromaDB reconnection...")
                
                old_status = self.text_handler.context_manager.is_chromadb_available()
                self.text_handler.context_manager.reset_chromadb_connection()
                new_status = self.text_handler.context_manager.is_chromadb_available()
                
                if new_status:
                    status_text = "✅ ChromaDB successfully connected!"
                elif old_status == new_status and not new_status:
                    status_text = "❌ ChromaDB still not reachable. Check Docker container."
                else:
                    status_text = "❌ ChromaDB connection failed."
                    
                self.bot.reply_to(message, status_text)
                
            except Exception as e:
                logger.error(f"Error during ChromaDB reconnection: {e}")
                self.bot.reply_to(message, f"❌ Reconnection error: {str(e)}")

        # Stats Command Handler
        @self.bot.message_handler(commands=['stats'])
        def send_stats(message):
            try:
                stats = self.monitor.get_system_stats()
                context_stats = self.text_handler.context_manager.get_context_stats()
                
                chromadb_status = "🟢 Connected" if context_stats['chromadb_enabled'] else "🔴 Not available"
                
                stats_text = f"""
📊 **System Statistics**

**Resources:**
- CPU: {stats.get('cpu_usage', 0):.1f}%
- Memory: {stats.get('memory_usage', {}).get('percent', 0):.1f}%
- Processes: {stats.get('process_count', 0)}

**Context (Files):**
- Active chats: {context_stats['total_chats']}
- Stored messages: {context_stats['total_lines']}
- Storage usage: {context_stats['total_size_mb']:.2f} MB

**ChromaDB:** {chromadb_status}
- Documents: {context_stats['chromadb_documents']}
- Chats: {context_stats['chromadb_chats']}
                """
                
                self.bot.reply_to(message, stats_text.strip(), parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Error retrieving statistics: {e}")
                self.bot.reply_to(message, "Error retrieving statistics.")

        # Register handlers for media content types
        @self.bot.message_handler(content_types=['photo'])
        def handle_photos(message):
            try:
                logger.info(f"Photo handler triggered - Photo count: {len(message.photo) if message.photo else 0}")
                self.file_handler.handle_message(message)
                self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing photo: {e}", exc_info=True)
                
        @self.bot.message_handler(content_types=['document'])
        def handle_documents(message):
            try:
                logger.info(f"Document handler triggered - Document: {message.document.file_name if message.document else 'None'}")
                self.file_handler.handle_message(message)
                self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing document: {e}", exc_info=True)
                
        @self.bot.message_handler(content_types=['voice'])
        def handle_voice(message):
            try:
                logger.info("Voice message handler triggered")
                self.file_handler.handle_message(message)
                self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing voice: {e}", exc_info=True)
                
        @self.bot.message_handler(content_types=['video', 'audio'])
        def handle_media(message):
            try:
                logger.info(f"Media handler triggered - Video: {bool(message.video)}, Audio: {bool(message.audio)}")
                self.file_handler.handle_message(message)
                self.text_handler.handle_message(message)  # Store context
            except Exception as e:
                logger.error(f"Error processing media: {e}", exc_info=True)

        # Finally register the general handler for text messages
        @self.bot.message_handler(func=lambda message: True)
        def handle_text_messages(message):
            try:
                logger.info(f"Text handler - Type: {message.content_type}, Text: {message.text}")
                
                # Only process text messages that are not commands
                if message.content_type == 'text' and (not message.text or not message.text.startswith('/')):
                    self.text_handler.handle_message(message)
                elif message.content_type == 'text' and message.text and message.text.startswith('/'):
                    logger.info(f"Command message handled by specific handler: {message.text}")
                else:
                    logger.info(f"Non-text message type {message.content_type} handled by specific handler")
            except Exception as e:
                logger.error(f"Error processing text message: {e}", exc_info=True)
                
    def _setup_signal_handlers(self):
        """Sets up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Signal {signum} received, shutting down bot...")
            self.shutdown()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def start_polling(self):
        """Starts bot polling"""
        logger.info(f"Bot started. Waiting for messages...")
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        try:
            self.bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            raise
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Gracefully shuts down the bot"""
        logger.info("Bot shutting down...")
        self.monitor.stop_monitoring()
        self.bot.stop_polling()
        logger.info("Bot successfully shut down")

if __name__ == "__main__":
    try:
        bot = TelegramBot()
        bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
