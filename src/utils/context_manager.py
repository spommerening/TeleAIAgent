"""
Context Management Utilities
Helper functions for context management
"""

import logging
import time
import os
import json
import uuid
from collections import deque
from config import Config

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        self.max_lines = Config.MAX_CONTEXT_LINES
        self.chroma_client = None
        self.chroma_collection = None
        self._init_chromadb()
    
    def _init_chromadb(self):
        """Initializes ChromaDB client and collection with retry logic"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB package not available - Context will only be stored in files")
            return
            
        max_retries = 5
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"ChromaDB connection attempt {attempt + 1}/{max_retries} to {Config.CHROMADB_HOST}:{Config.CHROMADB_PORT}")
                
                # Create ChromaDB client
                self.chroma_client = chromadb.HttpClient(
                    host=Config.CHROMADB_HOST,
                    port=Config.CHROMADB_PORT,
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Test the connection
                self.chroma_client.heartbeat()
                
                # Create or get collection
                try:
                    self.chroma_collection = self.chroma_client.get_collection(
                        name=Config.CHROMADB_COLLECTION_NAME
                    )
                    logger.info("✅ ChromaDB Collection found and connected")
                except:
                    self.chroma_collection = self.chroma_client.create_collection(
                        name=Config.CHROMADB_COLLECTION_NAME,
                        metadata={"description": "Chat context storage"}
                    )
                    logger.info("✅ ChromaDB Collection successfully created")
                
                return  # Success - exit function
                    
            except Exception as e:
                logger.warning(f"ChromaDB connection attempt {attempt + 1} failed: {e}")
                self.chroma_client = None
                self.chroma_collection = None
                
                if attempt < max_retries - 1:  # Not the last attempt
                    logger.info(f"Retry in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"❌ ChromaDB not reachable after {max_retries} attempts - Context will only be stored in files")
        
    def store_context(self, message, timestamp=None):
        """Stores context of a message in file and ChromaDB"""
        logger.info("Storing context")
        if isinstance(message, dict):
            if timestamp is None:
                raise ValueError("Timestamp must be provided for dictionary messages")
            timestamp_str = timestamp
        else:
            # Handle aiogram datetime object (not Unix timestamp like pyTelegramBotAPI)
            if hasattr(message.date, 'strftime'):  # It's already a datetime object
                timestamp_str = message.date.strftime('%Y-%m-%d %H:%M:%S')
            else:  # Fallback for Unix timestamp
                timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message.date))
        
        # Extract chat information
        chat_info = self._extract_chat_info(message)
        context_filename = os.path.join(Config.CONTEXT_DIR, f"chat_{chat_info['id']}.txt")
        
        # 1. Store in file (existing functionality)
        try:
            # Load existing lines
            lines = self._load_existing_lines(context_filename)
            
            # Create new line
            line = self._create_context_line(message, timestamp_str)
            
            lines.append(line)
            
            # Write back to file
            self._write_lines_to_file(context_filename, lines)
            
        except Exception as e:
            logger.error(f"Error writing to file: {e}")
        
        # 2. Store in parallel in ChromaDB
        self._store_context_chromadb(message, timestamp_str, chat_info)
    
    def _store_context_chromadb(self, message, timestamp_str, chat_info):
        """Stores context in ChromaDB"""
        if not self.chroma_collection:
            return
            
        try:
            # Extract message text
            if isinstance(message, dict):
                user_name = message['from']['first_name']
                text = message['text']
                user_id = message['from']['id']
                message_id = message['message_id']
                is_bot = message['from'].get('is_bot', False)
            else:
                user_name = message.from_user.first_name
                text = message.text
                user_id = message.from_user.id
                message_id = message.message_id
                is_bot = message.from_user.is_bot
            
            # Unique ID for the document
            doc_id = f"chat_{chat_info['id']}_msg_{message_id}_{int(time.time())}"
            
            # Create metadata
            metadata = {
                "chat_id": str(chat_info['id']),
                "chat_title": chat_info['title'],
                "chat_type": chat_info['type'],
                "user_id": str(user_id),
                "user_name": user_name,
                "message_id": str(message_id),
                "timestamp": timestamp_str,
                "date": time.strftime('%Y-%m-%d', time.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')),
                "is_bot": str(is_bot),
                "message_type": "bot_response" if is_bot else "user_message"
            }
            
            # Store in ChromaDB
            self.chroma_collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.debug(f"Context stored in ChromaDB: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error storing in ChromaDB: {e}")
    
    def load_chat_context(self, message):
        """Loads chat context for a message from file"""
        chat_info = self._extract_chat_info(message)
        context_filename = os.path.join(Config.CONTEXT_DIR, f"chat_{chat_info['id']}.txt")
        
        try:
            if os.path.exists(context_filename):
                with open(context_filename, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                return ""
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            return ""
    
    def load_chat_context_chromadb(self, message, limit=None):
        """Loads chat context from ChromaDB (Legacy - for compatibility only)"""
        if not self.chroma_collection:
            return ""
            
        chat_info = self._extract_chat_info(message)
        
        try:
            # Query all messages for this chat
            results = self.chroma_collection.get(
                where={"chat_id": str(chat_info['id'])},
                limit=limit or self.max_lines
            )
            
            if not results['documents']:
                return ""
            
            # Sort messages by timestamp
            messages = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                messages.append({
                    'timestamp': metadata['timestamp'],
                    'user_name': metadata['user_name'],
                    'text': doc
                })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x['timestamp'])
            
            # Format as text context
            context_lines = []
            for msg in messages:
                context_lines.append(f"[{msg['timestamp']}] {msg['user_name']}: {msg['text']}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Error loading from ChromaDB: {e}")
            return ""
    
    def load_relevant_context_chromadb(self, message, question):
        """Loads relevant chat context based on semantic search with token limiting"""
        if not Config.CONTEXT_SEARCH_ENABLED or not self.chroma_collection:
            logger.info("Semantic context search disabled or ChromaDB not available")
            return ""
            
        chat_info = self._extract_chat_info(message)
        
        try:
            # Debug: First retrieve all documents for this chat
            all_docs = self.chroma_collection.get(
                where={"chat_id": str(chat_info['id'])}
            )
            total_docs = len(all_docs['documents']) if all_docs['documents'] else 0
            
            # Count Bot vs User messages in database
            bot_docs = 0
            user_docs = 0
            if all_docs['metadatas']:
                for metadata in all_docs['metadatas']:
                    if metadata.get('is_bot', 'False') == 'True':
                        bot_docs += 1
                    else:
                        user_docs += 1
            
            logger.info(f"Chat {chat_info['id']}: {total_docs} documents total ({user_docs} User, {bot_docs} Bot)")
            
            # Semantic search for relevant messages
            results = self.chroma_collection.query(
                query_texts=[question],
                where={"chat_id": str(chat_info['id'])},
                n_results=Config.CONTEXT_SEARCH_RESULTS
            )
            
            if not results['documents'] or not results['documents'][0]:
                logger.info("No relevant context documents found")
                return ""
            
            # Collect relevant messages and filter by similarity
            relevant_messages = []
            bot_count = 0
            user_count = 0
            filtered_out = 0
            
            logger.debug(f"Analyzing {len(results['documents'][0])} search results...")
            
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = 1 - distance  # ChromaDB returns distance, we want similarity
                metadata = results['metadatas'][0][i]
                is_bot = metadata.get('is_bot', 'False') == 'True'
                message_type = metadata.get('message_type', 'user_message')
                
                logger.debug(f"Document {i}: similarity={similarity:.3f}, is_bot={is_bot}, threshold={Config.CONTEXT_MIN_SIMILARITY}")
                
                # Only messages above the similarity threshold
                if similarity >= Config.CONTEXT_MIN_SIMILARITY:
                    # Apply weighting for bot responses
                    weighted_similarity = similarity
                    if is_bot and Config.CONTEXT_INCLUDE_BOT_RESPONSES:
                        weighted_similarity *= Config.CONTEXT_BOT_WEIGHT
                        bot_count += 1
                        logger.debug(f"Bot message accepted: {doc[:50]}...")
                    else:
                        user_count += 1
                        logger.debug(f"User message accepted: {doc[:50]}...")
                    
                    relevant_messages.append({
                        'timestamp': metadata['timestamp'],
                        'user_name': metadata['user_name'],
                        'text': doc,
                        'similarity': similarity,
                        'weighted_similarity': weighted_similarity,
                        'is_bot': is_bot,
                        'message_type': message_type
                    })
                else:
                    filtered_out += 1
                    logger.debug(f"Document filtered (too low similarity): {similarity:.3f} < {Config.CONTEXT_MIN_SIMILARITY}")
            
            if not relevant_messages:
                logger.warning(f"No messages above similarity threshold found (filtered: {filtered_out})")
                # Fallback: If no semantically relevant messages were found,
                # use the newest messages (but still token-limited)
                if total_docs > 0:
                    logger.info("Fallback: Using newest messages for context")
                    fallback_results = self.chroma_collection.get(
                        where={"chat_id": str(chat_info['id'])},
                        limit=Config.CONTEXT_SEARCH_RESULTS
                    )
                    
                    if fallback_results['documents']:
                        # Convert to same format
                        for i, doc in enumerate(fallback_results['documents']):
                            metadata = fallback_results['metadatas'][i]
                            is_bot = metadata.get('is_bot', 'False') == 'True'
                            
                            relevant_messages.append({
                                'timestamp': metadata['timestamp'],
                                'user_name': metadata['user_name'],
                                'text': doc,
                                'similarity': 0.5,  # Neutral similarity for fallback
                                'weighted_similarity': 0.5,
                                'is_bot': is_bot,
                                'message_type': metadata.get('message_type', 'user_message')
                            })
                            
                            if is_bot:
                                bot_count += 1
                            else:
                                user_count += 1
                
                if not relevant_messages:
                    return ""
            
            logger.info(f"Relevant messages found: {user_count} User, {bot_count} Bot (filtered: {filtered_out})")
            
            # Sort by weighted similarity (best first)
            relevant_messages.sort(key=lambda x: x['weighted_similarity'], reverse=True)
            
            # Token-limited selection
            selected_context = self._select_context_by_tokens(relevant_messages)
            
            logger.info(f"Relevant context selected: {len(selected_context)} messages")
            
            # Return as formatted context
            if selected_context:
                context_lines = []
                for msg in selected_context:
                    # Clear marking of User vs. Bot messages
                    if msg.get('is_bot', False):
                        prefix = "🤖 AI-Antwort"
                        context_lines.append(f"[{msg['timestamp']}] {prefix} ({msg['user_name']}): {msg['text']}")
                    else:
                        prefix = "👤 User"
                        context_lines.append(f"[{msg['timestamp']}] {prefix} ({msg['user_name']}): {msg['text']}")
                return "\n".join(context_lines)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error in semantic context search: {e}")
            return ""
    
    def _select_context_by_tokens(self, messages):
        """Selects messages based on token limiting"""
        selected = []
        current_tokens = 0
        max_tokens = Config.CONTEXT_MAX_TOKENS
        bot_selected = 0
        user_selected = 0
        
        for msg in messages:
            # Format message with type indicator
            msg_type_indicator = "🤖 AI" if msg.get('is_bot', False) else "👤 User"
            message_text = f"[{msg['timestamp']}] {msg_type_indicator} {msg['user_name']}: {msg['text']}\n"
            
            # Rough token estimation: ~4 characters = 1 token
            estimated_tokens = len(message_text) / 4
            
            # Check if message still fits
            if current_tokens + estimated_tokens <= max_tokens:
                selected.append(msg)
                current_tokens += estimated_tokens
                
                if msg.get('is_bot', False):
                    bot_selected += 1
                    logger.debug(f"Bot response added (Tokens: +{estimated_tokens:.0f}, Total: {current_tokens:.0f})")
                else:
                    user_selected += 1
                    logger.debug(f"User message added (Tokens: +{estimated_tokens:.0f}, Total: {current_tokens:.0f})")
            else:
                logger.debug(f"Token limit reached ({current_tokens:.0f}/{max_tokens}), ignoring further messages")
                break
        
        # Sort by timestamp for chronological order
        selected.sort(key=lambda x: x['timestamp'])
        
        logger.info(f"Context selection: {len(selected)} messages ({user_selected} User + {bot_selected} Bot), ~{current_tokens:.0f} tokens")
        return selected
    
    def search_context_chromadb(self, query_text, chat_id=None, limit=10):
        """Searches ChromaDB for similar contexts"""
        if not self.chroma_collection:
            return []
            
        try:
            where_filter = {}
            if chat_id:
                where_filter["chat_id"] = str(chat_id)
            
            results = self.chroma_collection.query(
                query_texts=[query_text],
                where=where_filter if where_filter else None,
                n_results=limit
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            # Format results
            search_results = []
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                search_results.append({
                    'text': doc,
                    'metadata': metadata,
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in ChromaDB search: {e}")
            return []
    
    def _extract_chat_info(self, message):
        """Extracts chat information from message"""
        if isinstance(message, dict):
            return {
                'id': message['chat']['id'],
                'title': message['chat'].get('title', "Private"),
                'type': message['chat']['type']
            }
        else:
            return {
                'id': message.chat.id,
                'title': message.chat.title if message.chat.title else message.chat.first_name,
                'type': message.chat.type
            }
    
    def _load_existing_lines(self, filename):
        """Loads existing lines from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return deque(f.readlines(), maxlen=self.max_lines)
        except FileNotFoundError:
            return deque(maxlen=self.max_lines)
    
    def _create_context_line(self, message, timestamp_str):
        """Creates a context line"""
        if isinstance(message, dict):
            user_name = message['from']['first_name']
            text = message['text']
        else:
            user_name = message.from_user.first_name
            text = message.text
        
        return f"[{timestamp_str}] {user_name}: {text}\n"
    
    def _write_lines_to_file(self, filename, lines):
        """Writes lines to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def get_context_stats(self):
        """Returns statistics about stored contexts"""
        # File statistics
        context_files = [f for f in os.listdir(Config.CONTEXT_DIR) if f.startswith('chat_')]
        
        stats = {
            'total_chats': len(context_files),
            'total_lines': 0,
            'total_size_mb': 0,
            'chromadb_enabled': self.chroma_collection is not None,
            'chromadb_documents': 0,
            'chromadb_chats': 0
        }
        
        # Collect file statistics
        for file in context_files:
            file_path = os.path.join(Config.CONTEXT_DIR, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    stats['total_lines'] += len(lines)
                    
                file_size = os.path.getsize(file_path)
                stats['total_size_mb'] += file_size / (1024 * 1024)
                
            except Exception as e:
                logger.warning(f"Error reading file {file}: {e}")
        
        # Collect ChromaDB statistics
        if self.chroma_collection:
            try:
                # Total number of documents
                collection_count = self.chroma_collection.count()
                stats['chromadb_documents'] = collection_count
                
                # Number of unique chats
                if collection_count > 0:
                    all_metadata = self.chroma_collection.get()['metadatas']
                    unique_chats = set()
                    for meta in all_metadata:
                        unique_chats.add(meta.get('chat_id', 'unknown'))
                    stats['chromadb_chats'] = len(unique_chats)
                    
            except Exception as e:
                logger.warning(f"Error retrieving ChromaDB statistics: {e}")
        
        return stats
    
    def is_chromadb_available(self):
        """Checks if ChromaDB is available and connected"""
        return self.chroma_collection is not None
    
    def reset_chromadb_connection(self):
        """Resets the ChromaDB connection and attempts to reconnect"""
        logger.info("🔄 ChromaDB connection is being reset...")
        self.chroma_client = None
        self.chroma_collection = None
        self._init_chromadb()
        if self.is_chromadb_available():
            logger.info("✅ ChromaDB reconnection successful")
        else:
            logger.warning("❌ ChromaDB reconnection failed")
        
    def get_chat_history_chromadb(self, chat_id, days=7):
        """Gets chat history from ChromaDB for recent days"""
        if not self.chroma_collection:
            return []
            
        try:
            # Calculate date for filtering
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            results = self.chroma_collection.get(
                where={
                    "$and": [
                        {"chat_id": str(chat_id)},
                        {"date": {"$gte": cutoff_date}}
                    ]
                }
            )
            
            if not results['documents']:
                return []
            
            # Sort by timestamp
            messages = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                messages.append({
                    'timestamp': metadata['timestamp'],
                    'user_name': metadata['user_name'],
                    'text': doc,
                    'metadata': metadata
                })
            
            messages.sort(key=lambda x: x['timestamp'])
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []
