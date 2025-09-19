"""
Text Message Handler
Handler for text messages and bot interactions
"""

import logging
import time
from utils.context_manager import ContextManager
from utils.text_processor import TextProcessor
from utils.ai_client import AIClient

logger = logging.getLogger(__name__)

class TextHandler:
    def __init__(self, bot):
        self.bot = bot
        self.context_manager = ContextManager()
        self.text_processor = TextProcessor()
        self.ai_client = AIClient()
        self._bot_info = None  # Cache bot info
    
    async def get_bot_info(self):
        """Get bot info with caching"""
        if self._bot_info is None:
            self._bot_info = await self.bot.me()
        return self._bot_info
        
    async def handle_message(self, message):
        """Processes incoming messages"""
        # Store context
        self.context_manager.store_context(message)
        
        if not message.text:
            return
            
        logger.info(f"Text message received: {message.text}")
        
        if message.chat.type in ['group', 'supergroup']:
            await self._handle_group_message(message)
        elif message.chat.type == 'private':
            await self._handle_private_message(message)
    
    async def _handle_group_message(self, message):
        """Processes group messages"""
        bot_info = await self.get_bot_info()
        bot_username = bot_info.username
        
        # Check for bot mention
        if f'@{bot_username}' in message.text:
            question = message.text.replace(f'@{bot_username}', '').strip()
            logger.info(f"Bot mentioned: {question}")
            await self._answer_query(message, question)
            
        # Check for reply to bot message
        elif (message.reply_to_message and 
              message.reply_to_message.from_user.id == bot_info.id):
            logger.info(f"Reply to bot: {message.text}")
            await self._answer_query(message, message.text)
        else:
            logger.info(f"Group message ignored: {message.text}")
    
    async def _handle_private_message(self, message):
        """Processes private messages"""
        await self._answer_query(message, message.text)
    
    async def _answer_query(self, message, question):
        """Answers a question directly via the AI client"""
        start_time = time.time()
        
        try:
            # Load relevant chat context based on semantic search
            chat_context = self.context_manager.load_relevant_context_chromadb(message, question)
            
            # Fallback: If ChromaDB not available, use last context from file
            if not chat_context and not self.context_manager.is_chromadb_available():
                logger.warning("ChromaDB not available, using file fallback for context")
                file_context = self.context_manager.load_chat_context(message)
                # Limit file context to last lines
                if file_context:
                    lines = file_context.strip().split('\n')
                    # Take only last 20 lines for limited context
                    recent_lines = lines[-20:] if len(lines) > 20 else lines
                    chat_context = '\n'.join(recent_lines)
            
            # Create full context (only if relevant context was found)
            if chat_context:
                full_context = f"Relevant chat history:\n{chat_context}"
                logger.info("Context added for AI request")
            else:
                full_context = ""
                logger.info("No relevant context found, request without chat history")
            
            # Use AI client for response
            response = await self.ai_client.query_ai(question, full_context)
            
            elapsed_time = time.time() - start_time
            
            # Convert Markdown to HTML
            html_response = self.text_processor.markdown_to_telegram_html(response)
            
            logger.info(f"Response generated in {elapsed_time:.2f}s")
            
            # Store bot response in context
            await self._store_bot_response(message, html_response)
            
            # Send response
            await self._send_response(message, html_response)
            
        except Exception as e:
            logger.error(f"Error during response generation: {e}")
            error_response = "Sorry, there was a problem processing your request."
            await self._send_response(message, error_response)
    
    async def _store_bot_response(self, message, response):
        """Stores bot response in context"""
        bot_info = await self.get_bot_info()
        response_message = {
            'message_id': message.message_id,
            'from': {
                'id': bot_info.id,
                'is_bot': True,
                'first_name': bot_info.first_name,
                'username': bot_info.username
            },
            'chat': {
                'id': message.chat.id,
                'type': message.chat.type
            },
            'date': int(time.time()),
            'text': response,
            'entities': []
        }
        
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.context_manager.store_context(response_message, timestamp=timestamp)
    
    async def _send_response(self, message, response):
        """Sends the response split if necessary"""
        from aiogram import html
        
        # Split if too long
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                chunk = response[i:i+4096]
                if message.chat.type == 'private':
                    await self.bot.send_message(message.chat.id, chunk, parse_mode='HTML')
                else:
                    await message.reply(chunk, parse_mode='HTML')
        else:
            if message.chat.type == 'private':
                await self.bot.send_message(message.chat.id, response, parse_mode='HTML')
            else:
                await message.reply(response, parse_mode='HTML')
