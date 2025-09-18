# TeleAIAgent - Intelligent Telegram Chat Bot (AsyncIO)

TeleAIAgent is an extensible, AI-powered Telegram bot with **concurrent processing capabilities** for text, file, and multimedia processing. Built with **AsyncIO** for high-performance concurrent request handling, the bot leverages multiple AI backends (Perplexity AI, Ollama) and provides semantic search through ChromaDB integration for enhanced context-aware conversations.

## 🚀 **AsyncIO Implementation - Concurrent Processing**

⚡ **NEW**: The bot now supports **multiple simultaneous users** without blocking!
- **Concurrent AI requests** - multiple users can ask questions at the same time
- **Non-blocking file processing** - upload files while AI processes other requests  
- **Modern aiogram 3.x architecture** - event-driven message handling
- **Production-ready scalability** - handles group chats with multiple active users

> 📋 **[AsyncIO Documentation](doc/ASYNCIO_README.md)** - Complete technical details and migration guide

## 🏗️ Project Architecture

```
📦 TeleAIAgent Project Structure
├─ 🐳 Docker Infrastructure
│  ├─ docker-compose.yml          # Multi-container orchestration
│  ├─ Dockerfile-teleaiagent      # Bot container image
│  └─ .env                        # Environment variables
│
├─ 🚀 Core Application (src/) - **AsyncIO Architecture**
│  ├─ main.py                     # AsyncIO bot with aiogram 3.x & concurrent handlers
│  ├─ config.py                   # Central configuration
│  ├─ requirements.txt            # AsyncIO dependencies (aiogram, aiohttp, aiofiles)
│  ├─ test_chromadb.py            # ChromaDB integration test
│  ├─ test_async.py               # AsyncIO functionality & concurrent testing
│  │
│  ├─ 🔧 handlers/ (AsyncIO)      # Concurrent message processing
│  │  ├─ text_handler.py          # Async text & AI interactions
│  │  └─ file_handler.py          # Async file downloads (images, docs, audio)
│  │
│  └─ 🛠️ utils/ (AsyncIO)         # Async core services
│     ├─ ai_client.py             # Async AI backend manager (aiohttp)
│     ├─ context_manager.py       # Chat context & ChromaDB integration
│     ├─ text_processor.py        # Markdown/HTML conversion
│     └─ monitoring.py            # Async system monitoring
│
├─ 💾 Persistent Data (volumes/)
│  ├─ chromadb/                   # Vector database for RAG
│  ├─ teleaiagent/
│  │  ├─ context/                 # Chat history files
│  │  ├─ images/                  # Downloaded images
│  │  ├─ documents/               # Documents & PDFs
│  │  ├─ voice/                   # Voice messages
│  │  ├─ videos/                  # Video files
│  │  ├─ audio/                   # Audio files
│  │  ├─ logs/                    # Application logs
│  │  └─ cache/                   # Model cache
│  └─ ollama/                     # Local LLM models
│
└─ 📋 Documentation
   ├─ README.md                   # This documentation (AsyncIO)
   └─ doc/
      ├─ ASYNCIO_README.md        # AsyncIO implementation & concurrent processing
      ├─ CHROMADB_INTEGRATION.md  # ChromaDB integration guide
      └─ OLLAMA_BACKEND_SETUP.md  # Local AI backend configuration
```

## 🔄 AsyncIO Data Flow - Concurrent Processing

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Multiple      │    │   TeleAIAgent   │    │   Async AI      │
│   Telegram      │────│   (AsyncIO)     │────│   Client        │
│   Users/Groups  │    │   aiogram 3.x   │    │   aiohttp       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
   🔀 Multiple              🔀 Concurrent         🔀 Parallel
      Messages                  Handlers               API Calls
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Async Text/    │    │  Async Context  │    │  AI Backends    │
│  File Handlers  │────│  Manager        │    │ • Perplexity    │
│  (aiofiles)     │    │  + ChromaDB     │    │ • Ollama        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    🚀 Non-blocking       🧠 Smart Context      ⚡ Concurrent
      File Ops               Retrieval              Processing
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Async File     │    │  Concurrent     │    │   Async System  │
│  Storage        │────│  Response       │────│   Monitoring    │
│  (volumes/)     │    │  Processing     │    │   (asyncio)     │
│ • Documents     │    │ • Markdown→HTML │    │ • CPU/RAM       │
│ • Images/Video  │    │ • Text Chunking │    │ • ChromaDB      │
│ • Audio/Voice   │    │ • Multiple Users│    │ • Chat Stats    │
│ • Chat Context  │    │ • Queue-Free!   │    │ • Performance   │
└─────────────────┘    └─────────────────┘    └─────────────────┘

🎯 Key Benefits: Multiple users → Concurrent processing → No waiting queues!
```

## ⚙️ Core Features

### ⚡ **AsyncIO Concurrent Processing** 
- **Multiple Simultaneous Users**: No more waiting in queue!
- **Concurrent AI Requests**: Multiple questions processed simultaneously
- **Non-blocking File Operations**: Upload files while AI processes other requests
- **aiogram 3.x Architecture**: Modern, event-driven message handling
- **Production Scalability**: Handles high-traffic group chats efficiently

### 🤖 AI Integration
- **Multi-Engine Support**: Perplexity AI & Ollama local models
- **Context-Aware Responses**: Chat history is considered for better answers
- **Semantic Search**: ChromaDB-powered context retrieval
- **Automatic Model Management**: Ollama models are downloaded on-demand
- **Async API Calls**: Non-blocking AI requests with aiohttp

### 💬 Enhanced Chat Features
- **Concurrent Group Support**: Multiple users in groups processed simultaneously
- **Fast Private Chats**: Direct 1:1 communication without blocking
- **Multi-language**: German preferred, multi-language support
- **Markdown Support**: Rich-text formatting in responses
- **Intelligent Message Chunking**: Automatic splitting of long messages
- **Command System**: /start, /help, /status commands

### 📁 Async File Processing
- **Non-blocking Image Processing**: Automatic download and storage (aiofiles)
- **Concurrent Document Handling**: PDF, Word, Excel, etc. (multiple uploads simultaneously)
- **Parallel Audio/Video Processing**: Multimedia files processed without blocking
- **Async Voice Messages**: OGG format support with stream processing
- **Smart File Organization**: Structured storage by type with async operations
- **Upload While Processing**: Users can send multiple files while others process

### 🔍 Advanced Search & Context
- **ChromaDB Integration**: Semantic search in chat histories
- **RAG (Retrieval-Augmented Generation)**: Contextual AI answers
- **Persistent Storage**: All data survives container restarts
- **Metadata-based Filtering**: Efficient context queries

### 📊 AsyncIO Monitoring & Administration
- **Real-time System Statistics**: CPU, RAM, concurrent task monitoring
- **Concurrent Chat Analytics**: Message counts, parallel processing stats
- **Async ChromaDB Health**: Non-blocking connection status and document counts
- **Performance Monitoring**: AsyncIO task tracking, concurrent request metrics
- **Comprehensive Logging**: Debug and error logs with async rotation
- **Live Statistics**: /status command shows concurrent processing information

## 🚀 AsyncIO Installation & Setup

### Prerequisites (AsyncIO Optimized)
- Docker Engine 20.10+
- Docker Compose Plugin
- Git
- 4GB+ RAM recommended (handles concurrent processing efficiently)
- CPU with multiple cores (better for async operations)

### 1. Clone Repository
```bash
git clone https://github.com/spommerening/TeleAIAgent.git
cd TeleAIAgent
```

### 2. Configure Environment Variables
```bash
# Create/edit .env file
cp .env.example .env
nano .env

# Required API Keys:
TG_BOT_TOKEN="your_telegram_bot_token"
PERPLEXITY_API_KEY="your_perplexity_api_key"
AI_BACKEND="perplexity"  # or "ollama"
```

### 3. Start AsyncIO Services
```bash
# Start all services (AsyncIO Bot + ChromaDB + Ollama)
docker compose up -d

# Start with live logs (watch concurrent processing!)
docker compose up

# Quick test concurrent processing:
# Send multiple messages to your bot simultaneously - they'll all process at once!
```

## 🐳 AsyncIO Docker Management

### Container Operations (AsyncIO Optimized)
```bash
# Check status (AsyncIO bot performance)
docker compose ps

# View concurrent processing logs
docker compose logs -f teleaiagent  # Watch AsyncIO in action!
docker compose logs -f chromadb     # Concurrent database operations
docker compose logs -f ollama       # Parallel AI model requests

# Restart services
docker compose restart teleaiagent
docker compose restart ollama

# Stop specific service
docker compose stop teleaiagent

# Stop all services
docker compose down

# Stop with volume removal (WARNING: Data loss!)
docker compose down -v
```

### Image Management
```bash
# Build new version
docker compose build --no-cache teleaiagent

# Update images
docker compose pull

# Clean unused images
docker image prune

# Rebuild & restart
docker compose down && docker compose build && docker compose up -d
```

### AsyncIO Debugging & Maintenance
```bash
# Enter container (check AsyncIO processes)
docker compose exec teleaiagent bash
docker compose exec chromadb bash
docker compose exec ollama bash

# Check container resources (AsyncIO efficiency)
docker stats  # Watch CPU usage during concurrent processing

# Check volume contents
docker compose exec teleaiagent ls -la /app/context/
docker compose exec chromadb ls -la /chroma/chroma/
docker compose exec ollama ls -la /root/.ollama/

# Manage Ollama models
docker compose exec ollama ollama list
docker compose exec ollama ollama pull llama3.2
```

## 📡 AsyncIO AI Backend Configuration

### Supported AI Providers (Concurrent Processing)
- **Perplexity AI**: Main engine with integrated web search (async aiohttp requests)
- **Ollama**: Local LLM models (llama3.2, gemma, phi3, etc.) with concurrent model access

### Backend Selection
Set in `.env` file:
```bash
# Use Perplexity AI (cloud-based)
AI_BACKEND=perplexity
PERPLEXITY_API_KEY=your_api_key

# Or use Ollama (local models)
AI_BACKEND=ollama
# No API key required
```

### Model Configuration
In `src/config.py`:
```python
# Perplexity settings
PERPLEXITY_MODEL = "sonar"
PERPLEXITY_TEMPERATURE = 0.7

# Ollama settings  
OLLAMA_MODEL = "gemma3n:e2b"  # or llama3.2, phi3, etc.
OLLAMA_TEMPERATURE = 0.7
```

## 📋 Bot Commands

```
/start, /help     - Bot information and help
/stats           - System and chat statistics
/reconnect       - Rebuild ChromaDB connection
@botname <query> - Mention bot in groups
```

## 🔧 AsyncIO Development & Extension

### Local Development (AsyncIO Environment)
```bash
# Set up AsyncIO Python environment
cd src/
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows
pip install -r requirements.txt  # Includes aiogram 3.x, aiohttp, aiofiles

# Run AsyncIO bot locally (requires .env configuration)
python main.py  # Starts AsyncIO event loop with concurrent processing
```

### Testing AsyncIO Integration
```bash
# Test ChromaDB connectivity (async)
python test_chromadb.py

# Test concurrent processing
python test_async.py  # Validates AsyncIO performance and concurrent operations
```

### Adding New AsyncIO Features
1. **Extend Async Handlers**: `handlers/` for new message types (use async/await patterns)
2. **Add Async Utilities**: `utils/` for helper functions (aiohttp, aiofiles)
3. **Modify Configuration**: `config.py` for settings
4. **Follow AsyncIO Patterns**: Always use `async def` and `await` for I/O operations
5. **Concurrent Design**: Design features to handle multiple simultaneous users

### Key Configuration Options
All settings in `src/config.py`:
- AI backend selection and API endpoints
- ChromaDB connection settings
- File storage directories
- Bot personality and behavior
- Context search parameters

## 🔒 Security & Privacy

- **API Keys**: Secure management via environment variables
- **Container Isolation**: Services run in isolated containers
- **Volume Protection**: Persistent data outside containers
- **Log Rotation**: Automatic log cleanup (10MB max, 3 files)
- **Non-root Execution**: Bot runs as non-privileged user

## 🐛 AsyncIO Troubleshooting

### Common AsyncIO Issues

**Bot not responding or AsyncIO errors:**
```bash
docker compose logs teleaiagent | grep ERROR
docker compose logs teleaiagent | grep "asyncio"  # Check AsyncIO specific errors
docker compose restart teleaiagent
```

**ChromaDB connection issues:**
```bash
docker compose logs chromadb
# Check if port 8000 is accessible
curl http://localhost:8000/api/v1/heartbeat
```

**Ollama model problems:**
```bash
docker compose logs ollama
docker compose exec ollama ollama list
docker compose exec ollama ollama pull your-model
```

**Storage space full:**
```bash
# Clean logs
docker compose exec teleaiagent find /app/logs -name "*.log" -delete

# Clean Docker system
docker system prune -a

# Check volume usage
docker system df
```

**AsyncIO Performance issues:**
```bash
# Monitor concurrent processing resources
docker stats --no-stream

# Check AsyncIO performance with concurrent test
docker compose exec teleaiagent python test_async.py

# Check ChromaDB async performance
docker compose exec teleaiagent python test_chromadb.py
```

## 📊 Configuration Reference

### Environment Variables (.env)
```bash
# Required
TG_BOT_TOKEN=your_telegram_bot_token

# AI Backend (choose one)
AI_BACKEND=perplexity
PERPLEXITY_API_KEY=your_perplexity_key

# Optional
ANONYMIZED_TELEMETRY=TRUE
DEBUG=false
```

### Volume Mappings
- `./volumes/teleaiagent/context` → `/app/context` (Chat histories)
- `./volumes/teleaiagent/images` → `/app/images` (Downloaded images)
- `./volumes/teleaiagent/documents` → `/app/documents` (Documents)
- `./volumes/teleaiagent/voice` → `/app/voice` (Voice messages)
- `./volumes/teleaiagent/videos` → `/app/videos` (Videos)
- `./volumes/teleaiagent/audio` → `/app/audio` (Audio files)
- `./volumes/teleaiagent/logs` → `/app/logs` (Application logs)
- `./volumes/teleaiagent/cache` → `/root/.cache` (Model cache)
- `./volumes/chromadb` → `/chroma/chroma` (Vector database)
- `./volumes/ollama` → `/root/.ollama` (Ollama models)

### Network Configuration
- **Internal Network**: `mynetwork` (bridge)
- **ChromaDB Port**: 8000 (exposed to host)
- **Ollama Port**: 11434 (internal only)

## 📞 Support & Dependencies

### Key AsyncIO Dependencies
- **aiogram 3.13.0**: Modern async Telegram Bot API wrapper (replaces pyTelegramBotAPI)
- **aiohttp 3.10.10**: Async HTTP client for API requests
- **aiofiles ~23.2.1**: Non-blocking file operations
- **ChromaDB**: Vector database for semantic search (async compatible)
- **Ollama**: Local LLM inference with concurrent model access (optional)
- **Perplexity AI**: Cloud AI service with async requests (optional)

### AsyncIO System Requirements
- **CPU**: 2+ cores recommended (AsyncIO utilizes multiple cores efficiently)
- **RAM**: 4GB+ for optimal concurrent performance (8GB+ with Ollama)
- **Storage**: 10GB+ for data, logs, and models
- **Network**: Stable internet connection for concurrent API requests

### AsyncIO Architecture
- **Container Runtime**: Docker with compose orchestration + AsyncIO event loop
- **Concurrent Processing**: aiogram 3.x with async/await patterns throughout
- **Data Persistence**: Named volumes for data safety with async file operations
- **Service Discovery**: Internal DNS via Docker networks
- **Health Monitoring**: AsyncIO-aware health checks and concurrent logging
- **Event-Driven Design**: Non-blocking message handling with concurrent AI requests

---

**Developed with ❤️ for intelligent Telegram automation**

## License

MIT License - see [LICENSE](LICENSE) file for details.