# ChromaDB Integration for Context Manager

## Overview

The `ContextManager` has been extended to store chat context in parallel both in plain text files and in a ChromaDB instance. This enables:

- **Legacy Protection**: Continued storage in text files
- **Advanced Search**: Semantic search via ChromaDB
- **Better Scaling**: Efficient storage of large datasets
- **Structured Queries**: Metadata-based filtering

## Features

### Automatic Parallel Storage
Every chat message is automatically stored in both:
- Text file (`context/chat_[CHAT_ID].txt`) 
- ChromaDB Collection (`chat_context`)

### Extended Statistics
The `/stats` command now also shows ChromaDB information:
- Number of stored documents
- Number of unique chats in ChromaDB
- Connection status

### New Methods

#### `load_chat_context_chromadb(message, limit=None)`
Loads chat context from ChromaDB instead of text files.

#### `search_context_chromadb(query_text, chat_id=None, limit=10)`  
Semantic search in stored contexts.

#### `get_chat_history_chromadb(chat_id, days=7)`
Retrieves chat history from the last N days.

#### `is_chromadb_available()`
Checks ChromaDB availability.

#### `reset_chromadb_connection()`
Resets connection in case of problems.

## Setup

### 1. Install Dependencies
```bash
cd src/
pip install -r requirements.txt
```

### 2. Start Docker Container
```bash
docker-compose up -d chromadb
```

### 3. Run Test
```bash
python test_chromadb.py
```

## Configuration

In `config.py`:
```python
# ChromaDB Configuration  
CHROMADB_HOST = "chromadb"  # Docker service name
CHROMADB_PORT = 8000
CHROMADB_COLLECTION_NAME = "chat_context"
```

## Metadata Structure

Each message is stored with the following metadata:
- `chat_id`: Telegram Chat ID
- `chat_title`: Chat title or name
- `chat_type`: private/group/supergroup/channel
- `user_id`: Telegram User ID
- `user_name`: User's first name
- `message_id`: Telegram Message ID  
- `timestamp`: Timestamp (YYYY-MM-DD HH:MM:SS)
- `date`: Date (YYYY-MM-DD)

## Fallback Behavior

- In case of ChromaDB failure: Continued storage in text files
- Upon ChromaDB recovery: Automatic reconnection
- No functional degradation with disabled ChromaDB

## Performance

- Parallel storage minimally slower than pure text files
- ChromaDB search significantly faster than text search for larger datasets
- Efficient metadata filtering possible
