# Qdrant Integration for Context Manager

## Overview

The `ContextManager` has been migrated from ChromaDB to Qdrant to provide enhanced vector database capabilities. This migration maintains all existing functionality while providing:

- **Better Performance**: Qdrant's optimized vector storage and retrieval
- **Enhanced Scalability**: Better handling of large datasets
- **Improved Search**: More sophisticated semantic search capabilities
- **Legacy Protection**: Continued storage in text files as fallback
- **Backward Compatibility**: All existing ChromaDB methods still work

## Features

### Automatic Parallel Storage
Every chat message is automatically stored in both:
- Text file (`context/chat_[CHAT_ID].txt`) 
- Qdrant Collection (`chat_context`)

### Extended Statistics
The `/stats` command now shows Qdrant information:
- Number of stored documents
- Number of unique chats in Qdrant
- Connection status

### New Methods

#### `load_chat_context_qdrant(message, limit=None)`
Loads chat context from Qdrant instead of text files.

#### `search_context_qdrant(query_text, chat_id=None, limit=10)`  
Semantic search in stored contexts using vector similarity.

#### `load_relevant_context_qdrant(message, question)`
Advanced semantic search for contextually relevant messages.

#### `get_chat_history_qdrant(chat_id, days=7)`
Retrieves chat history from the last N days.

#### `is_qdrant_available()`
Checks Qdrant availability and connection status.

#### `reset_qdrant_connection()`
Resets connection in case of problems.

### Backward Compatibility Methods
All original ChromaDB methods are still available and automatically delegate to Qdrant:
- `load_chat_context_chromadb()` → `load_chat_context_qdrant()`
- `search_context_chromadb()` → `search_context_qdrant()`
- `is_chromadb_available()` → `is_qdrant_available()`
- etc.

## Setup

### 1. Install Dependencies

#### For Docker (Recommended - CPU-only):
```bash
docker-compose build
docker-compose up -d
```

#### For Local Development (CPU-only):
```bash
cd teleaiagent/
# Install CPU-only PyTorch first (compatible versions)
pip install torch==2.4.0+cpu torchvision==0.19.0+cpu torchaudio==2.4.0+cpu --index-url https://download.pytorch.org/whl/cpu
# Install remaining dependencies
pip install sentence-transformers==3.0.1
pip install -r requirements.txt
```

### 2. Start Docker Container
```bash
docker-compose up -d qdrant
```

### 3. Run Test
```bash
python test_qdrant.py
```

## Configuration

In `config.py`:
```python
# Qdrant Configuration  
QDRANT_HOST = "qdrant"  # Docker service name
QDRANT_PORT = 6333  # REST API port
QDRANT_GRPC_PORT = 6334  # gRPC API port (optional)
QDRANT_COLLECTION_NAME = "chat_context"
```

## Docker Configuration

In `docker-compose.yml`:
```yaml
qdrant:
  image: qdrant/qdrant:v1.11.0
  container_name: qdrant
  restart: unless-stopped
  ports:
    - "6333:6333"  # REST API
    - "6334:6334"  # gRPC API (optional)
  volumes:
    - ./volumes/qdrant/storage:/qdrant/storage
  environment:
    - QDRANT__SERVICE__HTTP_PORT=6333
    - QDRANT__SERVICE__GRPC_PORT=6334
```

## Payload Structure

Each message is stored with the following payload (metadata):
- `chat_id`: Telegram Chat ID
- `chat_title`: Chat title or name
- `chat_type`: private/group/supergroup/channel
- `user_id`: Telegram User ID
- `user_name`: User's first name
- `message_id`: Telegram Message ID  
- `timestamp`: Timestamp (YYYY-MM-DD HH:MM:SS)
- `date`: Date (YYYY-MM-DD)
- `is_bot`: "True" or "False"
- `message_type`: "bot_response" or "user_message"
- `text`: The actual message content

## Vector Embeddings

### Current Implementation
The current implementation uses a simple hash-based embedding for demonstration purposes. This ensures consistent vectors for the same text but doesn't provide semantic similarity.

### Production Recommendations
For production use, replace the `_get_embedding()` method with proper embedding models:

#### Option 1: OpenAI Embeddings
```python
import openai

def _get_embedding(self, text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']
```

#### Option 2: SentenceTransformers
```python
from sentence_transformers import SentenceTransformer

class ContextManager:
    def __init__(self):
        # ... existing code ...
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _get_embedding(self, text):
        return self.embedding_model.encode(text).tolist()
```

#### Option 3: Hugging Face Transformers
```python
from transformers import AutoTokenizer, AutoModel
import torch

def _get_embedding(self, text):
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
    
    return embeddings[0].tolist()
```

## Migration from ChromaDB

### Automatic Migration
If you have existing ChromaDB data, use the migration script:
```bash
python migrate_chromadb_to_qdrant.py
```

### Manual Steps
1. Stop the old ChromaDB container: `docker-compose down chromadb`
2. Start Qdrant: `docker-compose up -d qdrant`
3. Run migration script if needed
4. Test the integration: `python test_qdrant.py`

## Fallback Behavior

- **In case of Qdrant failure**: Continued storage in text files
- **Upon Qdrant recovery**: Automatic reconnection
- **No functional degradation**: All features work with disabled Qdrant
- **Backward compatibility**: All old ChromaDB methods still function

## Performance

- **Storage**: Parallel storage slightly slower than pure text files
- **Search**: Qdrant search significantly faster than text search for large datasets
- **Scalability**: Excellent performance with millions of vectors
- **Memory**: Efficient memory usage with on-disk storage
- **Filtering**: Fast metadata-based filtering

## Troubleshooting

### Connection Issues
```python
# Check if Qdrant is running
cm = ContextManager()
if not cm.is_qdrant_available():
    print("Qdrant not available")
    cm.reset_qdrant_connection()
```

### Collection Issues
If the collection doesn't exist, it will be automatically created on first connection.

### Embedding Issues
The current hash-based embedding is for development only. Replace with proper embeddings for production semantic search.

### Port Conflicts
If port 6333 is in use, modify the docker-compose.yml file:
```yaml
ports:
  - "6334:6333"  # Map to different host port
```

## API Reference

### Core Methods

#### `store_context(message, timestamp=None)`
Stores a message in both text file and Qdrant.

**Parameters:**
- `message`: Telegram message object or dictionary
- `timestamp`: Optional timestamp string (YYYY-MM-DD HH:MM:SS)

#### `search_context_qdrant(query_text, chat_id=None, limit=10)`
Performs semantic search in Qdrant.

**Parameters:**
- `query_text`: Text to search for
- `chat_id`: Optional chat ID to limit search scope
- `limit`: Maximum number of results (default: 10)

**Returns:** List of search results with text, metadata, and similarity scores.

#### `load_relevant_context_qdrant(message, question)`
Loads contextually relevant messages for a given question.

**Parameters:**
- `message`: Telegram message object for chat context
- `question`: Question to find relevant context for

**Returns:** Formatted context string with relevant messages.

### Statistics Methods

#### `get_context_stats()`
Returns comprehensive statistics about stored contexts.

**Returns:** Dictionary with file and Qdrant statistics:
```python
{
    'total_chats': 5,
    'total_lines': 1250,
    'total_size_mb': 2.3,
    'qdrant_enabled': True,
    'qdrant_documents': 1180,
    'qdrant_chats': 5
}
```

## Monitoring

### Health Checks
```python
# Basic health check
if cm.is_qdrant_available():
    print("✅ Qdrant is healthy")
else:
    print("❌ Qdrant is not available")

# Detailed statistics
stats = cm.get_context_stats()
print(f"Documents: {stats['qdrant_documents']}")
print(f"Chats: {stats['qdrant_chats']}")
```

### Logs
Monitor application logs for Qdrant connection and operation status:
```
INFO - ✅ Qdrant Collection found and connected
DEBUG - Context stored in Qdrant: chat_-1001234567890_msg_12345_1695123456
INFO - Relevant context selected: 5 messages (3 User + 2 Bot), ~1200 tokens
```