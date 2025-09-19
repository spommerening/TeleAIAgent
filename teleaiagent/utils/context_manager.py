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
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range
    from qdrant_client.http.exceptions import UnexpectedResponse
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        self.max_lines = Config.MAX_CONTEXT_LINES
        self.qdrant_client = None
        self.collection_exists = False
        self.embedding_model = None
        self._init_embedding_model()
        self._init_qdrant()
    
    def _init_embedding_model(self):
        """Initialize the embedding model"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight but effective model
                logger.info("🔄 Loading SentenceTransformer embedding model (CPU-optimized)...")
                
                # Initialize with CPU-only device map to ensure no GPU usage
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                
                # Check if we're actually using CPU
                import torch
                if torch.cuda.is_available():
                    logger.info("🔧 GPU detected but using CPU-only mode for compatibility")
                else:
                    logger.info("💻 Running in CPU-only mode (no GPU detected)")
                    
                logger.info("✅ SentenceTransformer model loaded successfully on CPU")
            except Exception as e:
                logger.error(f"❌ Failed to load SentenceTransformer model: {e}")
                self.embedding_model = None
        else:
            logger.warning("📦 SentenceTransformers not available - using fallback hash-based embeddings")
            self.embedding_model = None
    
    def _init_qdrant(self):
        """Initializes Qdrant client and collection with retry logic"""
        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant package not available - Context will only be stored in files")
            return
            
        max_retries = 5
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Qdrant connection attempt {attempt + 1}/{max_retries} to {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")
                
                # Create Qdrant client
                self.qdrant_client = QdrantClient(
                    host=Config.QDRANT_HOST,
                    port=Config.QDRANT_PORT,
                )
                
                # Test the connection
                self.qdrant_client.get_collections()
                
                # Create or get collection
                try:
                    collections = self.qdrant_client.get_collections()
                    collection_names = [col.name for col in collections.collections]
                    
                    if Config.QDRANT_COLLECTION_NAME in collection_names:
                        logger.info("✅ Qdrant Collection found and connected")
                        self.collection_exists = True
                    else:
                        # Create collection with vector configuration
                        # Using SentenceTransformers all-MiniLM-L6-v2 embedding size (384 dimensions)
                        self.qdrant_client.create_collection(
                            collection_name=Config.QDRANT_COLLECTION_NAME,
                            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                        )
                        logger.info("✅ Qdrant Collection successfully created")
                        self.collection_exists = True
                
                except Exception as e:
                    logger.error(f"Error with collection management: {e}")
                    self.qdrant_client = None
                    self.collection_exists = False
                    continue
                
                return  # Success - exit function
                    
            except Exception as e:
                logger.warning(f"Qdrant connection attempt {attempt + 1} failed: {e}")
                self.qdrant_client = None
                self.collection_exists = False
                
                if attempt < max_retries - 1:  # Not the last attempt
                    logger.info(f"Retry in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"❌ Qdrant not reachable after {max_retries} attempts - Context will only be stored in files")
        
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
        
        # 2. Store in parallel in Qdrant
        self._store_context_qdrant(message, timestamp_str, chat_info)
    
    def _get_embedding(self, text):
        """Generate semantic embedding using SentenceTransformers or fallback to hash-based"""
        # Handle None or empty text
        if not text:
            text = ""
        
        if self.embedding_model is not None:
            try:
                # Use SentenceTransformers for proper semantic embeddings
                embedding = self.embedding_model.encode(text, convert_to_tensor=False)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error generating embedding with SentenceTransformers: {e}")
                # Fall back to hash-based embedding
        
        # Fallback: hash-based embedding (for compatibility when SentenceTransformers fails)
        import hashlib
        import numpy as np
        
        logger.debug("Using fallback hash-based embedding")
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Create a 384-dimensional vector (matching all-MiniLM-L6-v2 output size)
        seed = int.from_bytes(hash_bytes[:4], byteorder='big')
        np.random.seed(seed)
        vector = np.random.randn(384).astype(np.float32)
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()

    def _store_context_qdrant(self, message, timestamp_str, chat_info):
        """Stores context in Qdrant"""
        if not self.qdrant_client or not self.collection_exists:
            return
            
        try:
            # Extract message text
            if isinstance(message, dict):
                user_name = message['from']['first_name']
                text = message.get('text') or message.get('caption', '')  # Handle None text
                user_id = message['from']['id']
                message_id = message['message_id']
                is_bot = message['from'].get('is_bot', False)
            else:
                user_name = message.from_user.first_name
                text = getattr(message, 'text', None) or getattr(message, 'caption', '') or ''  # Handle None text
                user_id = message.from_user.id
                message_id = message.message_id
                is_bot = message.from_user.is_bot
                
            # Skip storing if there's no meaningful text content
            if not text.strip():
                logger.debug(f"Skipping context storage for message without text content: {message_id}")
                return
            
            # Unique ID for the document
            doc_id = f"chat_{chat_info['id']}_msg_{message_id}_{int(time.time())}"
            
            # Create metadata (payload in Qdrant terminology)
            payload = {
                "chat_id": str(chat_info['id']),
                "chat_title": chat_info['title'],
                "chat_type": chat_info['type'],
                "user_id": str(user_id),
                "user_name": user_name,
                "message_id": str(message_id),
                "timestamp": timestamp_str,
                "date": time.strftime('%Y-%m-%d', time.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')),
                "is_bot": str(is_bot),
                "message_type": "bot_response" if is_bot else "user_message",
                "text": text  # Store text in payload for retrieval
            }
            
            # Generate embedding for the text
            vector = self._get_embedding(text)
            
            # Safety check for vector
            if not vector or not isinstance(vector, list):
                logger.warning(f"Invalid vector generated for text: {text[:50]}...")
                return
            
            # Create point
            point = PointStruct(
                id=hash(doc_id) & 0x7FFFFFFF,  # Convert to positive integer ID
                vector=vector,
                payload=payload
            )
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                points=[point]
            )
            
            logger.debug(f"Context stored in Qdrant: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error storing in Qdrant: {e}")
    
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
    
    def load_chat_context_qdrant(self, message, limit=None):
        """Loads chat context from Qdrant (Legacy - for compatibility only)"""
        if not self.qdrant_client or not self.collection_exists:
            return ""
            
        chat_info = self._extract_chat_info(message)
        
        try:
            # Query all messages for this chat
            response = self.qdrant_client.scroll(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chat_id",
                            match=MatchValue(value=str(chat_info['id']))
                        )
                    ]
                ),
                limit=limit or self.max_lines,
                with_payload=True,
                with_vectors=False
            )
            
            if not response[0]:  # No points found
                return ""
            
            # Sort messages by timestamp
            messages = []
            for point in response[0]:
                payload = point.payload
                messages.append({
                    'timestamp': payload['timestamp'],
                    'user_name': payload['user_name'],
                    'text': payload['text']
                })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x['timestamp'])
            
            # Format as text context
            context_lines = []
            for msg in messages:
                context_lines.append(f"[{msg['timestamp']}] {msg['user_name']}: {msg['text']}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Error loading from Qdrant: {e}")
            return ""
    
    def load_relevant_context_qdrant(self, message, question):
        """Loads relevant chat context based on semantic search with token limiting"""
        if not Config.CONTEXT_SEARCH_ENABLED or not self.qdrant_client or not self.collection_exists:
            logger.info("Semantic context search disabled or Qdrant not available")
            return ""
            
        chat_info = self._extract_chat_info(message)
        
        try:
            # Debug: First retrieve all documents for this chat
            all_response = self.qdrant_client.scroll(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chat_id",
                            match=MatchValue(value=str(chat_info['id']))
                        )
                    ]
                ),
                limit=10000,  # Large limit to get all for counting
                with_payload=True,
                with_vectors=False
            )
            
            total_docs = len(all_response[0])
            
            # Count Bot vs User messages in database
            bot_docs = 0
            user_docs = 0
            for point in all_response[0]:
                payload = point.payload
                if payload.get('is_bot', 'False') == 'True':
                    bot_docs += 1
                else:
                    user_docs += 1
            
            logger.info(f"Chat {chat_info['id']}: {total_docs} documents total ({user_docs} User, {bot_docs} Bot)")
            
            # Generate embedding for the question
            question_vector = self._get_embedding(question)
            
            # Semantic search for relevant messages
            search_results = self.qdrant_client.search(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                query_vector=question_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chat_id",
                            match=MatchValue(value=str(chat_info['id']))
                        )
                    ]
                ),
                limit=Config.CONTEXT_SEARCH_RESULTS,
                with_payload=True,
                with_vectors=False
            )
            
            if not search_results:
                logger.info("No relevant context documents found")
                return ""
            
            # Collect relevant messages and filter by similarity
            relevant_messages = []
            bot_count = 0
            user_count = 0
            filtered_out = 0
            
            logger.debug(f"Analyzing {len(search_results)} search results...")
            
            for result in search_results:
                # Qdrant returns score (similarity), not distance
                similarity = result.score
                payload = result.payload
                text = payload['text']
                is_bot = payload.get('is_bot', 'False') == 'True'
                message_type = payload.get('message_type', 'user_message')
                
                logger.debug(f"Document: similarity={similarity:.3f}, is_bot={is_bot}, threshold={Config.CONTEXT_MIN_SIMILARITY}")
                
                # Only messages above the similarity threshold
                if similarity >= Config.CONTEXT_MIN_SIMILARITY:
                    # Apply weighting for bot responses
                    weighted_similarity = similarity
                    if is_bot and Config.CONTEXT_INCLUDE_BOT_RESPONSES:
                        weighted_similarity *= Config.CONTEXT_BOT_WEIGHT
                        bot_count += 1
                        logger.debug(f"Bot message accepted: {text[:50]}...")
                    else:
                        user_count += 1
                        logger.debug(f"User message accepted: {text[:50]}...")
                    
                    relevant_messages.append({
                        'timestamp': payload['timestamp'],
                        'user_name': payload['user_name'],
                        'text': text,
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
                    fallback_response = self.qdrant_client.scroll(
                        collection_name=Config.QDRANT_COLLECTION_NAME,
                        scroll_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="chat_id",
                                    match=MatchValue(value=str(chat_info['id']))
                                )
                            ]
                        ),
                        limit=Config.CONTEXT_SEARCH_RESULTS,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    if fallback_response[0]:
                        # Convert to same format
                        for point in fallback_response[0]:
                            payload = point.payload
                            is_bot = payload.get('is_bot', 'False') == 'True'
                            
                            relevant_messages.append({
                                'timestamp': payload['timestamp'],
                                'user_name': payload['user_name'],
                                'text': payload['text'],
                                'similarity': 0.5,  # Neutral similarity for fallback
                                'weighted_similarity': 0.5,
                                'is_bot': is_bot,
                                'message_type': payload.get('message_type', 'user_message')
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
    
    def search_context_qdrant(self, query_text, chat_id=None, limit=10):
        """Searches Qdrant for similar contexts"""
        if not self.qdrant_client or not self.collection_exists:
            return []
            
        try:
            # Generate embedding for the query
            query_vector = self._get_embedding(query_text)
            
            # Build filter
            query_filter = None
            if chat_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="chat_id",
                            match=MatchValue(value=str(chat_id))
                        )
                    ]
                )
            
            # Perform search
            search_results = self.qdrant_client.search(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            if not search_results:
                return []
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    'text': result.payload['text'],
                    'metadata': result.payload,
                    'score': result.score  # Qdrant returns similarity score, not distance
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in Qdrant search: {e}")
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
            'qdrant_enabled': self.qdrant_client is not None and self.collection_exists,
            'qdrant_documents': 0,
            'qdrant_chats': 0
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
        
        # Collect Qdrant statistics
        if self.qdrant_client and self.collection_exists:
            try:
                # Total number of documents
                collection_info = self.qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
                stats['qdrant_documents'] = collection_info.points_count
                
                # Number of unique chats
                if collection_info.points_count > 0:
                    # Use scroll to get all points (with limit for safety)
                    all_response = self.qdrant_client.scroll(
                        collection_name=Config.QDRANT_COLLECTION_NAME,
                        limit=10000,  # Reasonable limit
                        with_payload=['chat_id'],
                        with_vectors=False
                    )
                    unique_chats = set()
                    for point in all_response[0]:
                        unique_chats.add(point.payload.get('chat_id', 'unknown'))
                    stats['qdrant_chats'] = len(unique_chats)
                    
            except Exception as e:
                logger.warning(f"Error retrieving Qdrant statistics: {e}")
        
        return stats
    
    def is_qdrant_available(self):
        """Checks if Qdrant is available and connected"""
        return self.qdrant_client is not None and self.collection_exists
    
    def reset_qdrant_connection(self):
        """Resets the Qdrant connection and attempts to reconnect"""
        logger.info("🔄 Qdrant connection is being reset...")
        self.qdrant_client = None
        self.collection_exists = False
        self._init_qdrant()
        if self.is_qdrant_available():
            logger.info("✅ Qdrant reconnection successful")
        else:
            logger.warning("❌ Qdrant reconnection failed")
        
    def get_chat_history_qdrant(self, chat_id, days=7):
        """Gets chat history from Qdrant for recent days"""
        if not self.qdrant_client or not self.collection_exists:
            return []
            
        try:
            # Calculate date for filtering
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # For now, get all messages for this chat and filter in Python
            # Qdrant's Range filter works with numeric values, not string dates
            response = self.qdrant_client.scroll(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chat_id",
                            match=MatchValue(value=str(chat_id))
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False
            )
            
            if not response[0]:
                return []
            
            # Filter by date and sort by timestamp
            messages = []
            for point in response[0]:
                payload = point.payload
                message_date = payload.get('date', '')
                
                # Filter messages by date (string comparison works for YYYY-MM-DD format)
                if message_date >= cutoff_date:
                    messages.append({
                        'timestamp': payload['timestamp'],
                        'user_name': payload['user_name'],
                        'text': payload['text'],
                        'metadata': payload
                    })
            
            messages.sort(key=lambda x: x['timestamp'])
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    # Backward compatibility methods (aliases for the old ChromaDB methods)
    def load_chat_context_chromadb(self, message, limit=None):
        """Backward compatibility - delegates to Qdrant"""
        return self.load_chat_context_qdrant(message, limit)
    
    def load_relevant_context_chromadb(self, message, question):
        """Backward compatibility - delegates to Qdrant"""
        return self.load_relevant_context_qdrant(message, question)
    
    def search_context_chromadb(self, query_text, chat_id=None, limit=10):
        """Backward compatibility - delegates to Qdrant"""
        return self.search_context_qdrant(query_text, chat_id, limit)
    
    def get_chat_history_chromadb(self, chat_id, days=7):
        """Backward compatibility - delegates to Qdrant"""
        return self.get_chat_history_qdrant(chat_id, days)
    
    def is_chromadb_available(self):
        """Backward compatibility - delegates to Qdrant"""
        return self.is_qdrant_available()
    
    def reset_chromadb_connection(self):
        """Backward compatibility - delegates to Qdrant"""
        return self.reset_qdrant_connection()
