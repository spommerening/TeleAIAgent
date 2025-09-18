"""
AI Client Manager - Management of AI API calls (AsyncIO)
"""

import logging
import aiohttp
import asyncio
import datetime
import re
import pytz
from config import Config

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        self.backend = Config.AI_BACKEND
        self.timezone = pytz.timezone(Config.DEFAULT_TIMEZONE)
        self._model_initialized = False
        
        if self.backend == 'perplexity':
            self.api_key = Config.PERPLEXITY_API_KEY
            self.api_url = Config.PERPLEXITY_API_URL
            self.model = Config.PERPLEXITY_MODEL
            self.temperature = Config.PERPLEXITY_TEMPERATURE
            self._model_initialized = True  # Perplexity doesn't need model initialization
        elif self.backend == 'ollama':
            self.url = Config.OLLAMA_URL
            self.api_url = Config.OLLAMA_API_URL.rstrip('/')
            self.model = Config.OLLAMA_MODEL
            self.temperature = Config.OLLAMA_TEMPERATURE
        else:
            raise ValueError(f"Unknown AI backend: {self.backend}")
    
    async def initialize(self):
        """Initialize the AI client (call this after creating the instance)"""
        if self.backend == 'ollama' and not self._model_initialized:
            await self._ensure_ollama_model()
            self._model_initialized = True
            
    async def _ensure_ollama_model(self):
        """Checks if the Ollama model is available and loads it if needed"""
        async with aiohttp.ClientSession() as session:
            try:
                # Check if model exists
                check_url = f"{self.url}/api/show"
                async with session.post(check_url, json={"name": self.model}) as response:
                    
                    if response.status in [404, 405]:  # Model not found or endpoint not available
                        logger.info(f"Model {self.model} is being downloaded...")
                        pull_url = f"{self.url}/api/pull"
                        
                        async with session.post(pull_url, json={"name": self.model}) as pull_response:
                            pull_response.raise_for_status()
                            
                            # Log Download progress
                            async for line in pull_response.content:
                                if line:
                                    progress = line.decode('utf-8')
                                    logger.debug(f"Download progress: {progress}")
                        
                        logger.info(f"Model {self.model} successfully downloaded")
                    else:
                        response.raise_for_status()
                        logger.info(f"Model {self.model} is already available")
                        
            except aiohttp.ClientError as e:
                error_msg = f"Error checking/downloading model: {e}"
                logger.error(error_msg)
                raise ValueError(f"Model {self.model} could not be initialized")
        
    def get_current_timestamp(self):
        """Returns current timestamp"""
        return datetime.datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
    
    def create_system_prompt(self, context=""):
        """Creates system prompt with context"""
        timestamp = self.get_current_timestamp()
        
        personality = Config.BOT_PERSONALITY
        system_prompt = f"""
        {personality}

        If the question requires current information, use the provided 
        context with web search results for answering.
        
        Current time: {timestamp}
        
        Context:
        {context}
        """
        logger.debug("-" * 80)
        logger.debug(f"System Prompt: {system_prompt}")
        logger.debug("-" * 80)
        
        return system_prompt.strip()
    
    def create_user_message(self, question):
        """Creates user message"""
        timestamp = self.get_current_timestamp()
        
        user_message = f"""
        Current time: {timestamp}
        Question: {question}
        """
        
        return user_message.strip()
    
    def estimate_tokens(self, text):
        """Estimates the number of tokens in a text
        
        Rough estimation: ~4 characters = 1 token for English/German
        """
        if not text:
            return 0
        # Remove extra whitespace and count characters
        clean_text = ' '.join(text.split())
        estimated_tokens = len(clean_text) / 4
        return int(estimated_tokens)
    
    def calculate_request_tokens(self, messages):
        """Calculates the total number of tokens for an API request"""
        total_tokens = 0
        token_breakdown = {}
        
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            role_tokens = self.estimate_tokens(role)
            content_tokens = self.estimate_tokens(content)
            message_tokens = role_tokens + content_tokens
            
            token_breakdown[role] = content_tokens
            total_tokens += message_tokens
        
        # Log token breakdown
        logger.debug(f"Token breakdown: {token_breakdown}")
        
        return total_tokens
    
    def process_response(self, response):
        """Processes AI response"""
        # Remove <think> tags
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = response.replace('<think>', '<i>').replace('</think>', '</i>')
        
        return response.strip()
    
    async def query_ai(self, question, context="", status_callback=None):
        """Sends request to AI API
        
        Args:
            question (str): The question to ask the AI
            context (str, optional): Additional context for the question
            status_callback (callable, optional): Async callback function for status messages
        """
        # Ensure the client is initialized
        if not self._model_initialized:
            await self.initialize()
            
        headers = {"Content-Type": "application/json"}
        messages = [
            {"role": "system", "content": self.create_system_prompt(context)},
            {"role": "user", "content": self.create_user_message(question)}
        ]
        
        if self.backend == 'perplexity':
            headers["Authorization"] = f"Bearer {self.api_key}"
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature
            }
        elif self.backend == 'ollama':
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature
                }
            }
        
        async with aiohttp.ClientSession() as session:
            try:
                # Calculate and output token count
                total_tokens = self.calculate_request_tokens(messages)
                logger.info(f"📊 Sending request to {self.model} - Estimated token count: {total_tokens}")
                start_time = datetime.datetime.now()
                
                api_endpoint = f"{self.url}/api/chat" if self.backend == 'ollama' else self.api_url
                
                # Send intermediate message for Ollama
                if self.backend == 'ollama' and status_callback:
                    await status_callback("I'm processing your question...")
                
                async with session.post(api_endpoint, headers=headers, json=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                
                if self.backend == 'perplexity':
                    ai_response = result['choices'][0]['message']['content']
                elif self.backend == 'ollama':
                    ai_response = result['message']['content']
                
                # Calculate processing time
                elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
                processed_response = self.process_response(ai_response)
                
                # Add processing time
                return f"{processed_response}\n\n⏱️ Processing time: {elapsed_time:.2f} seconds"
                
            except aiohttp.ClientError as e:
                error_msg = f"Error in API request: {e}"
                logger.error(error_msg)
                return "An error occurred with your API request."
                
            except (KeyError, IndexError) as e:
                logger.error(f"Error parsing API response: {e}")
                return "Error processing the response from the AI API."
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return "An unexpected error occurred."
