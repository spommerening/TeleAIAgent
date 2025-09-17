# TeleAIAgent - Intelligent Telegram Chat Bot

TeleAIAgent is an extensible, AI-powered Telegram bot with comprehensive features for text, file, and multimedia processing. The bot leverages multiple AI backends (Perplexity AI, Ollama) and provides semantic search through ChromaDB integration for enhanced context-aware conversations.

## 🏗️ Project Architecture

```
📦 TeleAIAgent Project Structure
├─ 🐳 Docker Infrastructure
│  ├─ docker-compose.yml          # Multi-container orchestration
│  ├─ Dockerfile-teleaiagent      # Bot container image
│  └─ .env                        # Environment variables
│
├─ 🚀 Core Application (src/)
│  ├─ main.py                     # Bot main entry point & handler setup
│  ├─ config.py                   # Central configuration
│  ├─ requirements.txt            # Python dependencies
│  ├─ test_chromadb.py            # ChromaDB integration test
│  │
│  ├─ 🔧 handlers/                # Message processing
│  │  ├─ text_handler.py          # Text & AI interactions
│  │  └─ file_handler.py          # File downloads (images, docs, audio)
│  │
│  └─ 🛠️ utils/                   # Core services
│     ├─ ai_client.py             # Central AI backend manager
│     ├─ context_manager.py       # Chat context & ChromaDB integration
│     ├─ text_processor.py        # Markdown/HTML conversion
│     └─ monitoring.py            # System monitoring
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
   ├─ README.md                   # This documentation
   └─ doc/
      └─ CHROMADB_INTEGRATION.md  # ChromaDB integration guide
```

## 🔄 Data Flow Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │────│   TeleAIAgent   │────│   AI Client     │
│   User/Group    │    │   (main.py)     │    │   Manager       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. Message            │ 3. AI Request         │
         │                       │                       ▼
         ▼                       ▼            ┌─────────────────┐
┌─────────────────┐    ┌─────────────────┐    │  AI Backends    │
│  Text/File      │    │  Context        │    │ • Perplexity    │
│  Handler        │────│  Manager        │    │ • Ollama        │
│                 │    │  + ChromaDB     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 2. Processing         │ 4. Relevant Context   │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  File Storage   │    │  Response       │    │   System        │
│  (volumes/)     │────│  Processing     │────│   Monitoring    │
│ • Documents     │    │ • Markdown→HTML │    │ • CPU/RAM       │
│ • Images/Video  │    │ • Text Chunking │    │ • ChromaDB      │
│ • Audio/Voice   │    │ • TTS Support   │    │ • Chat Stats    │
│ • Chat Context  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ⚙️ Core Features

### 🤖 AI Integration
- **Multi-Engine Support**: Perplexity AI & Ollama local models
- **Context-Aware Responses**: Chat history is considered for better answers
- **Semantic Search**: ChromaDB-powered context retrieval
- **Automatic Model Management**: Ollama models are downloaded on-demand

### 💬 Chat Features
- **Group Support**: Bot responds to @mentions and replies
- **Private Chats**: Direct 1:1 communication
- **Multi-language**: German preferred, multi-language support
- **Markdown Support**: Rich-text formatting in responses
- **Message Chunking**: Automatic splitting of long messages

### 📁 File Processing
- **Images**: Automatic download and storage
- **Documents**: PDF, Word, Excel, etc.
- **Audio/Video**: Multimedia file processing
- **Voice Messages**: OGG format support
- **File Organization**: Structured storage by type

### 🔍 Advanced Search & Context
- **ChromaDB Integration**: Semantic search in chat histories
- **RAG (Retrieval-Augmented Generation)**: Contextual AI answers
- **Persistent Storage**: All data survives container restarts
- **Metadata-based Filtering**: Efficient context queries

### 📊 Monitoring & Administration
- **System Statistics**: CPU, RAM, process monitoring
- **Chat Analytics**: Message counts, storage usage
- **ChromaDB Health**: Connection status and document counts
- **Comprehensive Logging**: Debug and error logs with rotation

## 🚀 Installation & Setup

### Prerequisites
- Docker Engine 20.10+
- Docker Compose Plugin
- Git
- 4GB+ RAM recommended

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

### 3. Start Services
```bash
# Start all services (Bot + ChromaDB + Ollama)
docker compose up -d

# Start with live logs
docker compose up
```

## 🐳 Docker Management

### Container Operations
```bash
# Check status
docker compose ps

# View logs
docker compose logs -f teleaiagent
docker compose logs -f chromadb
docker compose logs -f ollama

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

### Debugging & Maintenance
```bash
# Enter container
docker compose exec teleaiagent bash
docker compose exec chromadb bash
docker compose exec ollama bash

# Check container resources
docker stats

# Check volume contents
docker compose exec teleaiagent ls -la /app/context/
docker compose exec chromadb ls -la /chroma/chroma/
docker compose exec ollama ls -la /root/.ollama/

# Manage Ollama models
docker compose exec ollama ollama list
docker compose exec ollama ollama pull llama3.2
```

## 📡 AI Backend Configuration

### Supported AI Providers
- **Perplexity AI**: Main engine with integrated web search
- **Ollama**: Local LLM models (llama3.2, gemma, phi3, etc.)

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

## 🔧 Development & Extension

### Local Development
```bash
# Set up Python environment
cd src/
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run locally (requires .env configuration)
python main.py
```

### Testing ChromaDB Integration
```bash
# Test ChromaDB connectivity
python test_chromadb.py
```

### Adding New Features
1. **Extend Handlers**: `handlers/` for new message types
2. **Add Utilities**: `utils/` for helper functions
3. **Modify Configuration**: `config.py` for settings

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

## 🐛 Troubleshooting

### Common Issues

**Bot not responding:**
```bash
docker compose logs teleaiagent | grep ERROR
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

**Performance issues:**
```bash
# Monitor resources
docker stats --no-stream

# Check ChromaDB performance
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

### Key Dependencies
- **pyTelegramBotAPI**: Telegram Bot API wrapper
- **ChromaDB**: Vector database for semantic search
- **Ollama**: Local LLM inference (optional)
- **Perplexity AI**: Cloud AI service (optional)

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ for optimal performance (8GB+ with Ollama)
- **Storage**: 10GB+ for data, logs, and models
- **Network**: Stable internet connection for APIs

### Architecture
- **Container Runtime**: Docker with compose orchestration
- **Data Persistence**: Named volumes for data safety
- **Service Discovery**: Internal DNS via Docker networks
- **Health Monitoring**: Built-in health checks and logging

---

**Developed with ❤️ for intelligent Telegram automation**

## License

MIT License - see [LICENSE](LICENSE) file for details.