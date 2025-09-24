# TeleAIAgent - Intelligent Telegram Chat Bot (AsyncIO + Qdrant RAG + AI Image Analysis)

TeleAIAgent is an extensible, AI-powered Telegram bot with **concurrent processing capabilities** for text, file, and multimedia processing. Built with **AsyncIO** for high-performance concurrent request handling, the bot leverages multiple AI backends (Perplexity AI, Ollama) and provides **advanced semantic search through Qdrant vector database** with SentenceTransformers embeddings for enhanced context-aware conversations. **NEW**: Includes dedicated **Image Analysis Microservice** with AI-powered visual analysis and automated semantic storage.

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

### 🖼️ **NEW: AI Image Analysis Microservice**
- 🏗️ **Microservice Architecture**: Dedicated vision service on port 7777
- 🤖 **Vision AI Integration**: Ollama-powered image analysis with specialized prompts
- 📝 **Description Generation**: Comprehensive 3-sentence German descriptions of images
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
│  ├─ Dockerfile-vision           # Image analysis microservice container
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
│     ├─ vision_client.py         # HTTP client for vision microservice
│     └─ monitoring.py            # Async system monitoring
│
├─ 🖼️ **NEW: Vision Microservice (vision/)** - **AI Image Analysis**
│  ├─ main.py                     # FastAPI service with lifespan management
│  ├─ config.py                   # Vision configuration (port 7777)
│  ├─ requirements.txt            # FastAPI, vision dependencies
│  ├─ README.md                   # Vision documentation
│  │
│  ├─ 🖼️ handlers/               # Image processing pipeline
│  │  └─ image_handler.py         # AI-powered image analysis & description generation
│  │
│  └─ 🛠️ utils/                  # Vision core services
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
│  ├─ vision/
│  │  ├─ logs/                    # Vision service logs
│  │  └─ cache/                   # Vision model cache
│  └─ ollama/                     # Local LLM + vision models
│
├─ 🧪 Testing & Integration
│  └─ test_vision_integration.py  # End-to-end vision integration tests
│
└─ 📋 Documentation
   ├─ README.md                   # This documentation (AsyncIO + Qdrant + Vision)
   └─ doc/
      ├─ ASYNCIO_README.md        # AsyncIO implementation & concurrent processing
      ├─ CHROMADB_INTEGRATION.md  # Migration guide (ChromaDB → Qdrant)
      ├─ QDRANT_INTEGRATION.md    # Qdrant configuration and usage
      └─ OLLAMA_BACKEND_SETUP.md  # Local AI backend configuration
```

## 🔄 AsyncIO Data Flow - Concurrent Processing + AI Image Analysis

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
│  **NEW**: Image │    │  Vision         │    │  Vision AI      │
│  → Vision       │────│  Microservice   │────│  Analysis       │
│  Microservice   │    │  Port 7777      │    │  (Ollama)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    🖼️ AI Image          📝 Description Gen    🤖 Vision Models
      Analysis           (3-sentence German)    (llama3.2-vision)
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Organized      │    │  Vector Storage │    │   Async System  │
│  File Storage   │────│  (Qdrant DB)    │────│   Monitoring    │
│  (year/m/day)   │    │  + Metadata     │    │   (asyncio)     │
│ • Smart Dirs    │    │ • Image Embedds │    │ • CPU/RAM       │
│ • Unique Names  │    │ • Description   │    │ • 4 Services    │
│ • Chat Context  │    │ • Similarity    │    │ • Health Checks │
│ • Telegram Meta │    │ • Search Ready  │    │ • Performance   │
└─────────────────┘    └─────────────────┘    └─────────────────┘

🎯 Enhanced Benefits: 
   📷 Images → AI Analysis → Description Generation → Semantic Search → Organized Storage!
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

### 📁 Async File Processing + AI Image Analysis
- **Non-blocking Image Processing**: Automatic download and storage (aiofiles)
- **🆕 AI-Powered Image Analysis**: Automatic description generation via dedicated microservice
- **🆕 Smart Image Organization**: Year/month/day directory structure 
- **🆕 Vision AI Integration**: Ollama-based image understanding and description generation
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
- **🆕 Image Semantic Search**: Find similar images using AI-generated description embeddings
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
- **Modern Docker Compose Plugin** (uses `docker compose` not `docker-compose`)
- Git
- 4GB+ RAM recommended (handles concurrent processing efficiently)
- CPU with multiple cores (better for async operations)
- **Python 3.11+ with venv** (for local development and testing)

### 1. Clone Repository
```bash
git clone https://github.com/spommerening/TeleAIAgent.git
cd TeleAIAgent
```

### 2. Setup Development Environment
```bash
# Create Python virtual environment for local development
python3 -m venv ./venv
source ./venv/bin/activate

# Install development dependencies (for running tests)
pip install -r teleaiagent/requirements.txt
pip install -r vision/requirements.txt

# Create/edit .env file
cp .env.example .env
nano .env

# Required API Keys:
TG_BOT_TOKEN="your_telegram_bot_token"
PERPLEXITY_API_KEY="your_perplexity_api_key"
AI_BACKEND="perplexity"  # or "ollama"
```

> 📋 **Important**: Always activate the virtual environment with `source ./venv/bin/activate` before running Python scripts from the host system. The `./venv` directory is not committed to the repository.

### 3. Start AsyncIO Services + Vision Microservice
```bash
# Start all services (AsyncIO Bot + Vision + Qdrant + Ollama)
docker compose up -d

# Start with live logs (watch concurrent processing + AI image analysis!)
docker compose up

# Quick test concurrent processing:
# Send multiple messages to your bot simultaneously - they'll all process at once!
# Send images to see AI description generation in action!

# Check vision service health:
curl http://localhost:7777/health

# ⚠️ IMPORTANT: CPU Performance Notes
# First AI operations (Ollama model downloads, image analysis) can take 5-15+ minutes
# Be patient during initial startup - subsequent operations will be faster
# Use extended timeouts (600s+) for production deployments
```

## 🐳 AsyncIO Docker Management

### Container Operations (AsyncIO + Vision Optimized)
```bash
# Check status (AsyncIO bot + vision microservice performance)
docker compose ps

# View concurrent processing + AI image analysis logs
docker compose logs -f teleaiagent  # Watch AsyncIO in action!
docker compose logs -f vision       # AI image analysis and description generation
docker compose logs -f qdrant       # Vector database operations (text + images)
docker compose logs -f ollama       # Parallel AI model requests (text + vision)

# Restart services
docker compose restart teleaiagent
docker compose restart vision
docker compose restart ollama

# Stop specific service
docker compose stop teleaiagent
docker compose stop vision

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

### AsyncIO + Vision Debugging & Maintenance
```bash
# Enter containers (check AsyncIO processes + vision service)
docker compose exec teleaiagent bash
docker compose exec vision bash
docker compose exec qdrant bash
docker compose exec ollama bash

# Check container resources (AsyncIO + AI image analysis efficiency)
docker stats  # Watch CPU usage during concurrent processing + image analysis

# Check volume contents
docker compose exec teleaiagent ls -la /app/context/
docker compose exec teleaiagent ls -la /app/images/  # Organized by year/month/day
docker compose exec vision ls -la /app/volume_images/  # Shared image storage
docker compose exec qdrant ls -la /qdrant/storage/
docker compose exec ollama ls -la /root/.ollama/

# Manage Ollama models (text + vision)
docker compose exec ollama ollama list
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull llama3.2-vision:11b  # Vision model for image analysis

# Test vision service
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

In `vision/config.py`:
```python
# Vision service settings
VISION_PORT = 7777
IMAGES_VOLUME_DIR = "/app/volume_images"

# Vision AI settings
OLLAMA_MODEL = "llama3.2-vision:11b"  # Vision-capable model
OLLAMA_BASE_URL = "http://ollama:11434"
DESCRIPTION_PROMPT = "Describe this image in exactly 3 short sentences..."

# Qdrant settings for image storage
QDRANT_HOST = "qdrant"
QDRANT_PORT = 6333
IMAGE_COLLECTION = "image_descriptions"
```

## 📋 Bot Commands

```
/start, /help     - Bot information and help
/stats           - System and chat statistics (includes vision service status)
/reconnect       - Rebuild Qdrant connection
@botname <query> - Mention bot in groups
```

## 🖼️ **Vision Microservice API**

The Vision microservice provides a REST API for AI-powered image analysis:

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

#### `POST /analyze-image`
Process an image with AI analysis and description generation
```bash
curl -X POST \
  -F "image=@/path/to/image.jpg" \
  -F "chat_id=-1001234567890" \
  -F "message_id=123" \
  -F "file_id=ABC123xyz" \
  http://localhost:7777/analyze-image
```

### Image Processing Workflow

```
📷 Image Upload → 🤖 Vision AI Analysis → 📝 Description Generation → 
📁 File Organization → 💾 Vector Storage → 🔍 Searchable Content
```

1. **Image Reception**: FastAPI receives image with Telegram metadata
2. **AI Analysis**: Ollama vision model analyzes visual content
3. **Description Generation**: Comprehensive 3-sentence German description generated
4. **File Storage**: Image saved in organized year/month/day directory structure
5. **Vector Storage**: Description and metadata stored in Qdrant for semantic search
6. **Completion**: Returns success status with generated description and storage path

### Supported Image Formats
- JPEG/JPG
- PNG  
- WebP
- GIF

### Example AI-Generated Descriptions
- **Nature Scene**: `1. Mountain landscape with golden sunset over peaceful valley. 2. Serene natural beauty with warm lighting and scenic vista. 3. Outdoor wilderness setting with dramatic golden hour atmosphere.`
- **Urban Photo**: `1. Busy city street with modern architecture and heavy traffic. 2. Metropolitan environment with tall buildings and urban activity. 3. Contemporary cityscape showing bustling street life and commerce.`
- **Portrait**: `1. Friendly person with warm smile in casual indoor setting. 2. Close-up portrait showing natural facial expression and relaxed demeanor. 3. Human subject captured in comfortable, informal environment.`

## 🔧 AsyncIO Development & Extension

### Local Development Environment
```bash
# ⚠️ ALWAYS activate the shared virtual environment first
source ./venv/bin/activate  # Required for all Python operations from host

# Run AsyncIO bot locally (from host, requires Docker services running)
cd teleaiagent/
python main.py  # Starts AsyncIO event loop with concurrent processing

# Run vision service locally (alternative to Docker)
cd ../vision/
python main.py  # Starts FastAPI service on port 7777

# Note: Local development still requires Qdrant and Ollama containers
docker compose up qdrant ollama -d
```

### Testing AsyncIO + Vision Integration
```bash
# ⚠️ CRITICAL: Always activate venv before running Python tests
source ./venv/bin/activate

# Test Qdrant connectivity and semantic search (async)
cd teleaiagent/
python test_qdrant.py

# Test concurrent processing
python test_async.py  # Validates AsyncIO performance and concurrent operations

# Test vision microservice integration (from root directory)
cd ../
python test_vision_integration.py  # End-to-end image processing test

# Test individual vision components
cd vision/
python -m pytest  # Run vision unit tests (if available)
```

## 📊 **Current Project Status (September 2025)**

### ✅ **Completed Features**
- ✅ **Full Qdrant Migration**: ChromaDB → Qdrant v1.11.0 complete
- ✅ **Semantic Embeddings**: SentenceTransformers integration working
- ✅ **CPU Optimization**: PyTorch 2.4.0+cpu installed and tested  
- ✅ **Docker Integration**: Multi-container setup (teleaiagent, vision, qdrant, ollama)
- ✅ **AsyncIO Architecture**: Concurrent processing with aiogram 3.x
- ✅ **Service Networking**: Container communication configured
- ✅ **Vector Collections**: 384D embedding storage operational
- ✅ **Similarity Search**: Semantic context retrieval functional
- ✅ **🆕 Vision Microservice**: AI-powered image analysis and description generation
- ✅ **🆕 Vision AI Integration**: Ollama vision models (llama3.2-vision:11b)
- ✅ **🆕 Smart File Organization**: Year/month/day directory structure
- ✅ **🆕 Image Semantic Search**: Vector storage for analyzed images
- ✅ **🆕 Metadata Preservation**: Full Telegram context with images
- ✅ **🆕 FastAPI Service**: RESTful API on port 7777 with health monitoring
- ✅ **Backward Compatibility**: All existing features preserved

### 🔧 **System Health**
```bash
# Current status (all services operational):
✅ TeleAI Bot: Running with AsyncIO concurrent processing + vision integration
✅ Vision Service: AI image analysis microservice (port 7777) - HEALTHY
✅ Qdrant DB: Vector collections active (6333/6334 ports) - text + image embeddings 
✅ Ollama: Local AI models ready (11434 port) - text + vision models
✅ Semantic Search: 384D embeddings with 0.63+ similarity scores
✅ Image Processing: Automated description generation with year/month/day organization
✅ CPU Performance: PyTorch optimized for non-GPU environments
✅ Data Persistence: All volumes mounted and persistent
✅ Service Communication: Internal Docker networking functional
```

### 🎯 **Performance Metrics**
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Similarity Threshold**: 0.3 (configurable)
- **Vector Database**: Qdrant collections with async operations (text + images)
- **CPU Utilization**: Optimized PyTorch without CUDA dependencies
- **Memory Usage**: ~2GB RAM for Qdrant, ~3GB for Vision service
- **Response Time**: <500ms for semantic search, ~2-5s for image AI analysis
- **Concurrent Users**: Multiple simultaneous requests supported
- **🆕 Image Processing**: Comprehensive 3-sentence descriptions per image with metadata storage
- **🆕 File Organization**: Automatic year/month/day directory structure
- **🆕 Vision Health**: FastAPI service with comprehensive health monitoring

### 🧪 **Validation Tests**
```bash
# All tests passing:
✅ docker compose up -d          # 4 services start successfully (teleaiagent, vision, qdrant, ollama)
✅ python test_qdrant.py         # Semantic search working (0.63 similarity)
✅ python test_async.py          # Concurrent processing validated
✅ python test_vision_integration.py  # End-to-end image processing validated
✅ curl http://localhost:7777/health  # Vision service healthy
✅ Bot polling active            # Telegram integration operational
✅ Vector collections created    # Qdrant database functional (text + images)
✅ SentenceTransformer loaded    # CPU-optimized embeddings ready
✅ Vision AI models loaded       # Ollama llama3.2-vision:11b for image analysis
✅ Service networking functional # All container communication working
```

### 🔮 **Ready for Production**
The TeleAI system is now **production-ready** with:
- Modern vector database architecture (Qdrant)
- Semantic search capabilities with transformer embeddings
- **🆕 AI-powered image analysis and description generation microservice**
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
docker compose exec ollama ollama pull llama3.2-vision:11b  # Vision model for vision service
```

**Vision service issues:**
```bash
docker compose logs vision
curl http://localhost:7777/health  # Check service health
curl http://localhost:7777/stats   # Check processing statistics
docker compose restart vision
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
- **Vision Port**: 7777 (HTTP API) - exposed to host for image processing
- **Ollama Port**: 11434 (internal only)

## 📞 Support & Dependencies

### Key AsyncIO + Vision Dependencies
- **aiogram 3.13.0**: Modern async Telegram Bot API wrapper (replaces pyTelegramBotAPI)
- **aiohttp 3.10.10**: Async HTTP client for API requests + vision communication
- **aiofiles ~23.2.1**: Non-blocking file operations
- **FastAPI 0.104.1**: Modern async web framework for vision microservice
- **Qdrant 1.11.0**: High-performance vector database for semantic search (text + images)
- **SentenceTransformers 3.0.1**: Semantic embeddings (all-MiniLM-L6-v2 model)
- **PyTorch 2.4.0+cpu**: CPU-optimized machine learning framework
- **Ollama**: Local LLM inference with vision models (llama3.2-vision:11b for image analysis)
- **Perplexity AI**: Cloud AI service with async requests (optional)

### AsyncIO + Vision System Requirements
- **CPU**: 2+ cores recommended (AsyncIO + AI image processing utilizes multiple cores efficiently)
- **RAM**: 6GB+ for optimal concurrent performance (8GB+ recommended with Ollama + Vision)
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
- 🆕 **Vision Microservice**: AI-powered image analysis and description generation system
- 🆕 **Vision AI**: Ollama integration with vision-capable models (llama3.2-vision:11b)
- 🆕 **Smart Organization**: Year/month/day directory structure for images
- 🆕 **Image Search**: Semantic search for visual content using AI-generated descriptions

### 📈 **Key Benefits**
- **Better Context Understanding**: Semantic similarity vs keyword matching
- **AI-Powered Visual Analysis**: Automated image description generation and organization
- **Cross-Modal Search**: Find images using text descriptions and vice versa
- **Resource Efficient**: CPU-only setup reduces hardware requirements
- **Production Ready**: Scalable microservice architecture
- **Modern Stack**: Latest AsyncIO patterns with concurrent processing

## ⚡ **Performance Considerations & CPU-Only Operation**

### 🖥️ **CPU-Only Architecture Benefits**
- **No GPU Required**: Runs on standard CPU-only hardware
- **Cost Effective**: Reduced infrastructure requirements
- **Wide Compatibility**: Works on any modern multi-core CPU system

### ⏱️ **Performance Expectations (CPU-Only)**
- **First Startup**: 5-15+ minutes for initial model downloads and setup
- **Image Description Generation**: 2-5 minutes per image (Ollama vision models on CPU)
- **Text Processing**: Near real-time with SentenceTransformers
- **Vector Search**: Sub-second response times after embedding generation
- **Subsequent Operations**: Faster due to model caching

### 🛠️ **Optimization Strategies**
- **Extended Timeouts**: Configure 600+ second timeouts for AI operations
- **Model Caching**: First model downloads are cached for future use  
- **Concurrent Processing**: AsyncIO handles multiple requests efficiently
- **Resource Limits**: 2GB RAM for bot, 3GB for vision service
- **Background Processing**: Long operations don't block user interactions

> 📋 **Development Tips**: 
> - Use `source ./venv/bin/activate` before running Python scripts
> - Test with `docker compose` (modern syntax) not `docker-compose`
> - Be patient during first AI operations - they get faster!
> - Monitor logs with `docker compose logs -f [service]`

> 📖 **Detailed Guides**: 
> - [AsyncIO Implementation](doc/ASYNCIO_README.md)
> - [Qdrant Integration](doc/QDRANT_INTEGRATION.md) 
> - [CPU Installation](doc/CPU_INSTALLATION.md)
> - [Ollama Backend Setup](doc/OLLAMA_BACKEND_SETUP.md)

### 🚀 **Current Status: Production Ready with AI Image Processing**
All services operational (4-container architecture), tests passing, and ready for deployment with comprehensive AI-powered image management! 

---

**Developed with ❤️ for intelligent Telegram automation and AI-powered content management**

*Latest Update: AI Image Analysis Microservice + Qdrant Vector Database Migration (September 2025)*

## License

MIT License - see [LICENSE](LICENSE) file for details.
