# TeleAIAgent - Intelligent Telegram Chat Bot (AsyncIO + Qdrant RAG + AI Image Tagging)

TeleAIAgent is an extensible, AI-powered Telegram bot with **concurrent processing capabilities** for text, file, and multimedia processing. Built with **AsyncIO** for high-performance concurrent request handling, the bot leverages multiple AI backends (Perplexity AI, Ollama) and provides **advanced semantic search through Qdrant vector database** with SentenceTransformers embeddings for enhanced context-aware conversations. **NEW**: Includes dedicated **Image Tagging Microservice** with AI-powered visual analysis and automated semantic storage.

## 🚀 **AsyncIO Implementation - Concurrent Processing**

⚡ **NEW**: The bot now supports **multiple simultaneous users** without blocking!
- **Concurrent AI requests** - multiple users can ask questions at the same time
- **Non-blocking file processing** - upload files while AI processes other requests  
- **Modern aiogram 3.x architecture** - event-driven message handling
- **Production-ready scalability** - handles group chats with multiple active users

> 📋 **[AsyncIO Documentation](doc/ASYNCIO_README.md)** - Complete technical details and migration guide

## 🎯 **Latest Update: Qdrant Vector Database Migration**

🔥 **MAJOR UPGRADE**: Successfully migrated from ChromaDB to **Qdrant** for enhanced semantic search!

### ✨ **New Features (September 2025)**
- 🚀 **Qdrant v1.11.0**: High-performance vector database with 384D semantic embeddings
- 🧠 **SentenceTransformers**: Advanced semantic understanding with `all-MiniLM-L6-v2` model
- 💻 **CPU-Optimized**: PyTorch CPU-only installation (no GPU required)
- ⚡ **Semantic Search**: Find relevant context by meaning, not just keywords
- 🎯 **Similarity Scoring**: Configurable relevance threshold (0.3 default)
- 🔄 **Backward Compatible**: All existing functionality preserved
- 📊 **Better Performance**: Improved vector similarity search with optimized embeddings

### 🖼️ **NEW: AI Image Tagging Microservice**
- 🏗️ **Microservice Architecture**: Dedicated tagger service on port 7777
- 🤖 **Vision AI Integration**: Ollama-powered image analysis with specialized prompts
- 🏷️ **Automated Tagging**: 5-10 descriptive tags per image (objects, mood, setting, actions)
- 📁 **Smart Organization**: Year/month/day directory structure for images
- 🔍 **Semantic Image Search**: Find similar images using vector similarity
- 💾 **Metadata Preservation**: Full Telegram context stored with embeddings
- 🐳 **Containerized**: FastAPI service with health monitoring and error recovery

### 🔧 **Technical Improvements**
- **Vector Dimensions**: 384D embeddings for efficient CPU processing
- **Memory Efficiency**: Resource-optimized for containers without GPU
- **Service Architecture**: Docker containerized Qdrant service (ports 6333/6334)
- **Async Integration**: Non-blocking semantic search with AsyncIO patterns
- **Data Persistence**: Vector collections survive container restarts

### 📈 **Migration Benefits**
- **Better Context Retrieval**: Semantic similarity instead of keyword matching
- **Improved AI Responses**: More relevant context leads to better answers
- **Resource Efficient**: CPU-only setup reduces hardware requirements
- **Production Ready**: Battle-tested Qdrant database with proven scalability
- **Future-Proof**: Modern vector database architecture for AI applications

## 🏗️ Project Architecture

```
📦 TeleAIAgent Project Structure
├─ 🐳 Docker Infrastructure
│  ├─ docker-compose.yml          # Multi-container orchestration (4 services)
│  ├─ Dockerfile-teleaiagent      # Bot container image
│  ├─ Dockerfile-tagger           # Image tagging microservice container
│  └─ .env                        # Environment variables
│
├─ 🚀 Core Application (teleaiagent/) - **AsyncIO Architecture**
│  ├─ main.py                     # AsyncIO bot with aiogram 3.x & concurrent handlers
│  ├─ config.py                   # Central configuration
│  ├─ requirements.txt            # AsyncIO dependencies (aiogram, aiohttp, aiofiles)
│  ├─ test_qdrant.py              # Qdrant semantic search test
│  ├─ test_async.py               # AsyncIO functionality & concurrent testing
│  │
│  ├─ 🔧 handlers/ (AsyncIO)      # Concurrent message processing
│  │  ├─ text_handler.py          # Async text & AI interactions
│  │  └─ file_handler.py          # Async file downloads + tagger integration
│  │
│  └─ 🛠️ utils/ (AsyncIO)         # Async core services
│     ├─ ai_client.py             # Async AI backend manager (aiohttp)
│     ├─ context_manager.py       # Chat context & Qdrant integration
│     ├─ text_processor.py        # Markdown/HTML conversion
│     ├─ tagger_client.py         # HTTP client for tagger microservice
│     └─ monitoring.py            # Async system monitoring
│
├─ 🏷️ **NEW: Tagger Microservice (tagger/)** - **AI Image Analysis**
│  ├─ main.py                     # FastAPI service with lifespan management
│  ├─ config.py                   # Tagger configuration (port 7777)
│  ├─ requirements.txt            # FastAPI, vision dependencies
│  ├─ README.md                   # Tagger documentation
│  │
│  ├─ 🖼️ handlers/               # Image processing pipeline
│  │  └─ image_handler.py         # AI-powered image analysis & tagging
│  │
│  └─ 🛠️ utils/                  # Tagger core services
│     ├─ ollama_client.py         # Vision AI client for image analysis
│     ├─ qdrant_client.py         # Vector storage for image embeddings
│     └─ file_manager.py          # Organized file storage (year/month/day)
│
├─ 💾 Persistent Data (volumes/)
│  ├─ qdrant/                     # Vector database for RAG + image embeddings
│  ├─ teleaiagent/
│  │  ├─ context/                 # Chat history files
│  │  ├─ images/                  # **Shared**: Downloaded + organized images
│  │  ├─ documents/               # Documents & PDFs
│  │  ├─ voice/                   # Voice messages
│  │  ├─ videos/                  # Video files
│  │  ├─ audio/                   # Audio files
│  │  ├─ logs/                    # TeleAIAgent logs
│  │  └─ cache/                   # Model cache
│  ├─ tagger/
│  │  ├─ logs/                    # Tagger service logs
│  │  └─ cache/                   # Tagger model cache
│  └─ ollama/                     # Local LLM + vision models
│
├─ 🧪 Testing & Integration
│  └─ test_tagger_integration.py  # End-to-end tagger integration tests
│
└─ 📋 Documentation
   ├─ README.md                   # This documentation (AsyncIO + Qdrant + Tagger)
   └─ doc/
      ├─ ASYNCIO_README.md        # AsyncIO implementation & concurrent processing
      ├─ CHROMADB_INTEGRATION.md  # Migration guide (ChromaDB → Qdrant)
      ├─ QDRANT_INTEGRATION.md    # Qdrant configuration and usage
      └─ OLLAMA_BACKEND_SETUP.md  # Local AI backend configuration
```

## 🔄 AsyncIO Data Flow - Concurrent Processing + AI Image Tagging

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
│  (aiofiles)     │    │  + Qdrant RAG   │    │ • Ollama        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    🚀 Non-blocking      🧠 Semantic Search     ⚡ Concurrent
      File Ops           (384D Embeddings)        Processing
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  **NEW**: Image │    │  Tagger         │    │  Vision AI      │
│  → Tagger       │────│  Microservice   │────│  Analysis       │
│  Microservice   │    │  Port 7777      │    │  (Ollama)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    🖼️ AI Image          🏷️ Auto Tagging      🤖 Vision Models
      Analysis           (5-10 tags/image)      (gemma3n:e2b)
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Organized      │    │  Vector Storage │    │   Async System  │
│  File Storage   │────│  (Qdrant DB)    │────│   Monitoring    │
│  (year/m/day)   │    │  + Metadata     │    │   (asyncio)     │
│ • Smart Dirs    │    │ • Image Embedds │    │ • CPU/RAM       │
│ • Unique Names  │    │ • Tag Vectors   │    │ • 4 Services    │
│ • Chat Context  │    │ • Similarity    │    │ • Health Checks │
│ • Telegram Meta │    │ • Search Ready  │    │ • Performance   │
└─────────────────┘    └─────────────────┘    └─────────────────┘

🎯 Enhanced Benefits: 
   📷 Images → AI Analysis → Smart Tags → Semantic Search → Organized Storage!
   🚀 Multiple users → Concurrent processing → No waiting queues → AI-powered insights!
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
- **Semantic Search**: Qdrant-powered vector similarity retrieval
- **Automatic Model Management**: Ollama models are downloaded on-demand
- **Async API Calls**: Non-blocking AI requests with aiohttp

### 💬 Enhanced Chat Features
- **Concurrent Group Support**: Multiple users in groups processed simultaneously
- **Fast Private Chats**: Direct 1:1 communication without blocking
- **Multi-language**: German preferred, multi-language support
- **Markdown Support**: Rich-text formatting in responses
- **Intelligent Message Chunking**: Automatic splitting of long messages
- **Command System**: /start, /help, /status commands

### 📁 Async File Processing + AI Image Tagging
- **Non-blocking Image Processing**: Automatic download and storage (aiofiles)
- **🆕 AI-Powered Image Analysis**: Automatic tagging via dedicated microservice
- **🆕 Smart Image Organization**: Year/month/day directory structure 
- **🆕 Vision AI Integration**: Ollama-based image understanding and tagging
- **🆕 Metadata Preservation**: Full Telegram context stored with images
- **Concurrent Document Handling**: PDF, Word, Excel, etc. (multiple uploads simultaneously)
- **Parallel Audio/Video Processing**: Multimedia files processed without blocking
- **Async Voice Messages**: OGG format support with stream processing
- **Upload While Processing**: Users can send multiple files while others process

### 🔍 Advanced Semantic Search & RAG + Image Search
- **Qdrant Vector Database**: High-performance vector similarity search
- **SentenceTransformers**: 384-dimensional semantic embeddings (all-MiniLM-L6-v2)
- **CPU-Optimized**: PyTorch CPU-only for efficient resource usage
- **RAG (Retrieval-Augmented Generation)**: Context-aware AI responses
- **Semantic Context Retrieval**: Find relevant chat history by meaning, not keywords
- **🆕 Image Semantic Search**: Find similar images using AI-generated tag embeddings
- **🆕 Visual Content Discovery**: Search images by description, objects, mood, setting
- **🆕 Cross-Modal Search**: Text queries return relevant images and conversations
- **Persistent Storage**: All data survives container restarts
- **Similarity Threshold Filtering**: Configurable relevance scoring (default: 0.3)

### 📊 AsyncIO Monitoring & Administration
- **Real-time System Statistics**: CPU, RAM, concurrent task monitoring
- **Concurrent Chat Analytics**: Message counts, parallel processing stats
- **Async Qdrant Health**: Non-blocking connection status and vector collection stats
- **Semantic Search Metrics**: Embedding performance and similarity scores
- **Performance Monitoring**: AsyncIO task tracking, concurrent request metrics
- **Comprehensive Logging**: Debug and error logs with async rotation
- **Live Statistics**: /status command shows concurrent processing and vector DB information

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

### 3. Start AsyncIO Services + Tagger Microservice
```bash
# Start all services (AsyncIO Bot + Tagger + Qdrant + Ollama)
docker compose up -d

# Start with live logs (watch concurrent processing + AI image tagging!)
docker compose up

# Quick test concurrent processing:
# Send multiple messages to your bot simultaneously - they'll all process at once!
# Send images to see AI tagging in action!

# Check tagger service health:
curl http://localhost:7777/health
```

## 🐳 AsyncIO Docker Management

### Container Operations (AsyncIO + Tagger Optimized)
```bash
# Check status (AsyncIO bot + tagger microservice performance)
docker compose ps

# View concurrent processing + AI tagging logs
docker compose logs -f teleaiagent  # Watch AsyncIO in action!
docker compose logs -f tagger       # AI image analysis and tagging
docker compose logs -f qdrant       # Vector database operations (text + images)
docker compose logs -f ollama       # Parallel AI model requests (text + vision)

# Restart services
docker compose restart teleaiagent
docker compose restart tagger
docker compose restart ollama

# Stop specific service
docker compose stop teleaiagent
docker compose stop tagger

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

### AsyncIO + Tagger Debugging & Maintenance
```bash
# Enter containers (check AsyncIO processes + tagger service)
docker compose exec teleaiagent bash
docker compose exec tagger bash
docker compose exec qdrant bash
docker compose exec ollama bash

# Check container resources (AsyncIO + AI tagging efficiency)
docker stats  # Watch CPU usage during concurrent processing + image analysis

# Check volume contents
docker compose exec teleaiagent ls -la /app/context/
docker compose exec teleaiagent ls -la /app/images/  # Organized by year/month/day
docker compose exec tagger ls -la /app/volume_images/  # Shared image storage
docker compose exec qdrant ls -la /qdrant/storage/
docker compose exec ollama ls -la /root/.ollama/

# Manage Ollama models (text + vision)
docker compose exec ollama ollama list
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull gemma3n:e2b  # Vision model for image tagging

# Test tagger service
curl -X GET http://localhost:7777/health
curl -X GET http://localhost:7777/stats
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
In `teleaiagent/config.py`:
```python
# Perplexity settings
PERPLEXITY_MODEL = "sonar"
PERPLEXITY_TEMPERATURE = 0.7

# Ollama settings  
OLLAMA_MODEL = "gemma3n:e2b"  # or llama3.2, phi3, etc.
OLLAMA_TEMPERATURE = 0.7
```

In `tagger/config.py`:
```python
# Tagger service settings
TAGGER_PORT = 7777
IMAGES_VOLUME_DIR = "/app/volume_images"

# Vision AI settings
OLLAMA_MODEL = "gemma3n:e2b"  # Vision-capable model
OLLAMA_BASE_URL = "http://ollama:11434"
TAGGING_PROMPT = "Analyze this image and generate 5-10 descriptive tags..."

# Qdrant settings for image storage
QDRANT_HOST = "qdrant"
QDRANT_PORT = 6333
IMAGE_COLLECTION = "image_tags"
```

## 📋 Bot Commands

```
/start, /help     - Bot information and help
/stats           - System and chat statistics (includes tagger service status)
/reconnect       - Rebuild Qdrant connection
@botname <query> - Mention bot in groups
```

## 🏷️ **Tagger Microservice API**

The Tagger microservice provides a REST API for AI-powered image analysis:

### API Endpoints

#### `GET /health`
Check service health status
```bash
curl http://localhost:7777/health
```

#### `GET /stats`
Get processing statistics and service information
```bash
curl http://localhost:7777/stats
```

#### `POST /tag-image`
Process an image with AI analysis and tagging
```bash
curl -X POST \
  -F "image=@/path/to/image.jpg" \
  -F "chat_id=-1001234567890" \
  -F "message_id=123" \
  -F "file_id=ABC123xyz" \
  http://localhost:7777/tag-image
```

### Image Processing Workflow

```
📷 Image Upload → 🤖 Vision AI Analysis → 🏷️ Tag Generation → 
📁 File Organization → 💾 Vector Storage → 🔍 Searchable Content
```

1. **Image Reception**: FastAPI receives image with Telegram metadata
2. **AI Analysis**: Ollama vision model analyzes visual content
3. **Tag Generation**: 5-10 descriptive tags generated (objects, mood, setting, actions)
4. **File Storage**: Image saved in organized year/month/day directory structure
5. **Vector Storage**: Tags and metadata stored in Qdrant for semantic search
6. **Completion**: Returns success status with generated tags and storage path

### Supported Image Formats
- JPEG/JPG
- PNG  
- WebP
- GIF

### Example AI-Generated Tags
- **Nature Scene**: `mountain, sunset, landscape, peaceful, golden_hour, valley, scenic, outdoor, natural_beauty, serene`
- **Urban Photo**: `city, street, architecture, people, traffic, modern, buildings, urban_life, busy, metropolitan`
- **Portrait**: `person, smile, indoor, casual, friendly, portrait, human, face, expression, close_up`

## 🔧 AsyncIO Development & Extension

### Local Development (AsyncIO + Tagger Environment)
```bash
# Set up AsyncIO Python environment for TeleAIAgent
cd teleaiagent/
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows
pip install -r requirements.txt  # Includes aiogram 3.x, aiohttp, aiofiles

# Run AsyncIO bot locally (requires .env configuration)
python main.py  # Starts AsyncIO event loop with concurrent processing

# Set up Tagger microservice environment (separate terminal)
cd tagger/
python -m venv tagger_venv
source tagger_venv/bin/activate
pip install -r requirements.txt  # Includes FastAPI, vision dependencies

# Run tagger service locally
python main.py  # Starts FastAPI service on port 7777
```

### Testing AsyncIO + Tagger Integration
```bash
# Test Qdrant connectivity and semantic search (async)
cd teleaiagent/
python test_qdrant.py

# Test concurrent processing
python test_async.py  # Validates AsyncIO performance and concurrent operations

# Test tagger microservice integration
cd ../  # Root directory
python test_tagger_integration.py  # End-to-end image processing test

# Test individual tagger components
cd tagger/
python -m pytest  # Run tagger unit tests (if available)
```

## 📊 **Current Project Status (September 2025)**

### ✅ **Completed Features**
- ✅ **Full Qdrant Migration**: ChromaDB → Qdrant v1.11.0 complete
- ✅ **Semantic Embeddings**: SentenceTransformers integration working
- ✅ **CPU Optimization**: PyTorch 2.4.0+cpu installed and tested  
- ✅ **Docker Integration**: Multi-container setup (teleaiagent, tagger, qdrant, ollama)
- ✅ **AsyncIO Architecture**: Concurrent processing with aiogram 3.x
- ✅ **Service Networking**: Container communication configured
- ✅ **Vector Collections**: 384D embedding storage operational
- ✅ **Similarity Search**: Semantic context retrieval functional
- ✅ **🆕 Tagger Microservice**: AI-powered image analysis and tagging
- ✅ **🆕 Vision AI Integration**: Ollama vision models (gemma3n:e2b)
- ✅ **🆕 Smart File Organization**: Year/month/day directory structure
- ✅ **🆕 Image Semantic Search**: Vector storage for tagged images
- ✅ **🆕 Metadata Preservation**: Full Telegram context with images
- ✅ **🆕 FastAPI Service**: RESTful API on port 7777 with health monitoring
- ✅ **Backward Compatibility**: All existing features preserved

### 🔧 **System Health**
```bash
# Current status (all services operational):
✅ TeleAI Bot: Running with AsyncIO concurrent processing + tagger integration
✅ Tagger Service: AI image analysis microservice (port 7777) - HEALTHY
✅ Qdrant DB: Vector collections active (6333/6334 ports) - text + image embeddings 
✅ Ollama: Local AI models ready (11434 port) - text + vision models
✅ Semantic Search: 384D embeddings with 0.63+ similarity scores
✅ Image Processing: Automated tagging with year/month/day organization
✅ CPU Performance: PyTorch optimized for non-GPU environments
✅ Data Persistence: All volumes mounted and persistent
✅ Service Communication: Internal Docker networking functional
```

### 🎯 **Performance Metrics**
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Similarity Threshold**: 0.3 (configurable)
- **Vector Database**: Qdrant collections with async operations (text + images)
- **CPU Utilization**: Optimized PyTorch without CUDA dependencies
- **Memory Usage**: ~2GB RAM for Qdrant, ~3GB for Tagger service
- **Response Time**: <500ms for semantic search, ~2-5s for image AI analysis
- **Concurrent Users**: Multiple simultaneous requests supported
- **🆕 Image Processing**: 5-10 AI tags per image with metadata storage
- **🆕 File Organization**: Automatic year/month/day directory structure
- **🆕 Tagger Health**: FastAPI service with comprehensive health monitoring

### 🧪 **Validation Tests**
```bash
# All tests passing:
✅ docker compose up -d          # 4 services start successfully (teleaiagent, tagger, qdrant, ollama)
✅ python test_qdrant.py         # Semantic search working (0.63 similarity)
✅ python test_async.py          # Concurrent processing validated
✅ python test_tagger_integration.py  # End-to-end image processing validated
✅ curl http://localhost:7777/health  # Tagger service healthy
✅ Bot polling active            # Telegram integration operational
✅ Vector collections created    # Qdrant database functional (text + images)
✅ SentenceTransformer loaded    # CPU-optimized embeddings ready
✅ Vision AI models loaded       # Ollama gemma3n:e2b for image analysis
✅ Service networking functional # All container communication working
```

### 🔮 **Ready for Production**
The TeleAI system is now **production-ready** with:
- Modern vector database architecture (Qdrant)
- Semantic search capabilities with transformer embeddings
- **🆕 AI-powered image analysis and tagging microservice**
- **🆕 Automated visual content organization and search**
- **🆕 Vision AI integration with semantic storage**
- CPU-optimized performance (no GPU requirements)
- Full AsyncIO concurrent processing
- Comprehensive Docker containerization (4-service architecture)
- Robust error handling and monitoring
- Scalable microservice architecture

### Adding New AsyncIO Features
1. **Extend Async Handlers**: `handlers/` for new message types (use async/await patterns)
2. **Add Async Utilities**: `utils/` for helper functions (aiohttp, aiofiles)
3. **Modify Configuration**: `config.py` for settings
4. **Follow AsyncIO Patterns**: Always use `async def` and `await` for I/O operations
5. **Concurrent Design**: Design features to handle multiple simultaneous users

### Key Configuration Options
All settings in `src/config.py`:
- AI backend selection and API endpoints
- Qdrant connection settings and similarity thresholds
- SentenceTransformers model configuration
- File storage directories
- Bot personality and behavior
- Semantic search parameters

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

**Qdrant connection issues:**
```bash
docker compose logs qdrant
# Check if port 6333 is accessible
curl http://localhost:6333/collections
```

**Ollama model problems:**
```bash
docker compose logs ollama
docker compose exec ollama ollama list
docker compose exec ollama ollama pull your-model
docker compose exec ollama ollama pull gemma3n:e2b  # Vision model for tagger
```

**Tagger service issues:**
```bash
docker compose logs tagger
curl http://localhost:7777/health  # Check service health
curl http://localhost:7777/stats   # Check processing statistics
docker compose restart tagger
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

# Check Qdrant semantic search performance
docker compose exec teleaiagent python test_qdrant.py
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
- `./volumes/qdrant` → `/qdrant/storage` (Vector database)
- `./volumes/ollama` → `/root/.ollama` (Ollama models)

### Network Configuration
- **Internal Network**: `mynetwork` (bridge)
- **Qdrant Ports**: 6333 (HTTP API), 6334 (gRPC) - exposed to host
- **Tagger Port**: 7777 (HTTP API) - exposed to host for image processing
- **Ollama Port**: 11434 (internal only)

## 📞 Support & Dependencies

### Key AsyncIO + Tagger Dependencies
- **aiogram 3.13.0**: Modern async Telegram Bot API wrapper (replaces pyTelegramBotAPI)
- **aiohttp 3.10.10**: Async HTTP client for API requests + tagger communication
- **aiofiles ~23.2.1**: Non-blocking file operations
- **FastAPI 0.104.1**: Modern async web framework for tagger microservice
- **Qdrant 1.11.0**: High-performance vector database for semantic search (text + images)
- **SentenceTransformers 3.0.1**: Semantic embeddings (all-MiniLM-L6-v2 model)
- **PyTorch 2.4.0+cpu**: CPU-optimized machine learning framework
- **Ollama**: Local LLM inference with vision models (gemma3n:e2b for image analysis)
- **Perplexity AI**: Cloud AI service with async requests (optional)

### AsyncIO + Tagger System Requirements
- **CPU**: 2+ cores recommended (AsyncIO + AI image processing utilizes multiple cores efficiently)
- **RAM**: 6GB+ for optimal concurrent performance (8GB+ recommended with Ollama + Tagger)
- **Storage**: 15GB+ for data, logs, models, and organized image storage
- **Network**: Stable internet connection for concurrent API requests

### AsyncIO Architecture
- **Container Runtime**: Docker with compose orchestration + AsyncIO event loop
- **Concurrent Processing**: aiogram 3.x with async/await patterns throughout
- **Data Persistence**: Named volumes for data safety with async file operations
- **Service Discovery**: Internal DNS via Docker networks
- **Health Monitoring**: AsyncIO-aware health checks and concurrent logging
- **Event-Driven Design**: Non-blocking message handling with concurrent AI requests

---

## 🎉 **Major Updates Summary (September 2025)**

This project has been **successfully upgraded** with major architectural improvements:

### ✅ **Completed Migration & New Features**
- 🚀 **Vector Database**: ChromaDB → Qdrant v1.11.0
- 🧠 **Semantic Embeddings**: Integrated SentenceTransformers with 384D vectors  
- 💻 **CPU Optimization**: PyTorch 2.4.0+cpu (no GPU required)
- 🐳 **Docker Integration**: Full containerized setup with service networking
- ⚡ **Performance**: Improved semantic search with similarity scoring
- 🔄 **Compatibility**: All existing features preserved and enhanced
- 🆕 **Tagger Microservice**: AI-powered image analysis and tagging system
- 🆕 **Vision AI**: Ollama integration with vision-capable models (gemma3n:e2b)
- 🆕 **Smart Organization**: Year/month/day directory structure for images
- 🆕 **Image Search**: Semantic search for visual content using AI-generated tags

### 📈 **Key Benefits**
- **Better Context Understanding**: Semantic similarity vs keyword matching
- **AI-Powered Visual Analysis**: Automated image tagging and organization
- **Cross-Modal Search**: Find images using text descriptions and vice versa
- **Resource Efficient**: CPU-only setup reduces hardware requirements
- **Production Ready**: Scalable microservice architecture
- **Modern Stack**: Latest AsyncIO patterns with concurrent processing

### 🚀 **Current Status: Production Ready with AI Image Processing**
All services operational (4-container architecture), tests passing, and ready for deployment with comprehensive AI-powered image management! 

---

**Developed with ❤️ for intelligent Telegram automation and AI-powered content management**

*Latest Update: AI Image Tagging Microservice + Qdrant Vector Database Migration (September 2025)*

## License

MIT License - see [LICENSE](LICENSE) file for details.

MIT License - see [LICENSE](LICENSE) file for details.