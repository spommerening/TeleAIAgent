# Vision Microservice

The Vision microservice is responsible for AI-powered image analysis, description generation, and storage with semantic search capabilities.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TeleAIAgent   │────│   Vision        │────│   Ollama        │
│   (Image from   │    │   Service       │    │   (AI Analysis) │
│   Telegram)     │    │   Port 7777     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   File System   │    │   Qdrant DB     │
                       │   (Year/Month/  │    │   (Vector       │
                       │    Day dirs)    │    │    Search)      │
                       └─────────────────┘    └─────────────────┘
```

## Features

### 🤖 AI-Powered Image Analysis
- **Ollama Integration**: Uses vision-capable models for image understanding
- **Specialized Prompts**: Optimized prompts for generating descriptive image analysis
- **Description Generation**: Comprehensive 3-sentence descriptions covering objects, mood, setting, actions
- **CPU Optimized**: Efficient processing without GPU requirements

### 🗄️ Semantic Storage & Search
- **Qdrant Vector Database**: High-performance vector similarity search
- **SentenceTransformers**: 384-dimensional semantic embeddings
- **Metadata Rich**: Complete Telegram context preserved
- **Similar Image Search**: Find related images by semantic similarity

### 📁 Organized File Storage
- **Date Hierarchy**: Automatic year/month/day directory structure
- **Unique Naming**: Chat ID + Message ID + File ID naming convention
- **Volume Persistence**: Docker volume mapping for data persistence
- **Multiple Formats**: Support for JPEG, PNG, WebP, GIF formats

### 🔗 Microservice Integration
- **FastAPI**: Modern, async REST API
- **Health Monitoring**: Comprehensive health checks and statistics
- **Error Handling**: Robust error recovery and logging
- **Docker Native**: Containerized deployment with proper networking

## API Endpoints

### `POST /analyze-image`
Process an image and generate description.

**Request:**
- `image`: Multipart file upload
- `telegram_metadata`: JSON string with message metadata

**Response:**
```json
{
  "status": "success",
  "message": "Image processed and analyzed successfully",
  "result": {
    "document_id": "image_123456_12345_1695123456",
    "description": "1. Anime-style woman with pink hair wearing red outfit. 2. Standing in cozy living room with white couch. 3. Bright cheerful atmosphere with warm lighting.",
    "file_path": "/app/volume_images/2025/09/19/chat_123456_msg_12345_abc.jpg",
    "file_size": 156789,
    "chat_id": "123456",
    "message_id": "12345",
    "processed_at": "2025-09-19T10:30:00"
  }
}
```

### `GET /health`
Service health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "details": {
    "service": "healthy",
    "ollama": "healthy", 
    "qdrant": "healthy",
    "file_system": "healthy"
  }
}
```

### `GET /stats`
Comprehensive service statistics.

**Response:**
```json
{
  "service": {
    "name": "vision",
    "version": "1.0.0",
    "status": "running"
  },
  "qdrant": {
    "collection_name": "image_descriptions",
    "total_images": 1250,
    "unique_chats": 15,
    "vector_size": 384,
    "status": "healthy"
  },
  "storage": {
    "total_images": 1250,
    "total_size_mb": 245.7,
    "directory_count": 23
  }
}
```

## Configuration

### Environment Variables
All configuration is inherited from the main `.env` file:

```bash
# AI Backend (shared with teleaiagent)
AI_BACKEND=perplexity  # or ollama

# Database (shared)
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### Service Configuration (`vision/config.py`)
```python
# Service
SERVICE_PORT = 7777

# Ollama
OLLAMA_URL = "http://ollama:11434"
OLLAMA_MODEL = "llama3.2-vision:11b"  # Vision-capable model

# Qdrant
QDRANT_COLLECTION_NAME = "image_descriptions"  # Separate from chat context

# File Storage
IMAGES_VOLUME_DIR = "/app/volume_images"  # Mapped to docker volume

# Processing
MAX_IMAGE_SIZE_MB = 10
SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "webp", "gif"]
```

## Data Flow

1. **Image Receipt**: TeleAIAgent forwards image + metadata to vision:7777
2. **AI Analysis**: Ollama analyzes image and generates comprehensive description
3. **Path Generation**: Create year/month/day directory structure
4. **File Storage**: Save image to organized filesystem location
5. **Vector Storage**: Store description + metadata in Qdrant with embeddings
6. **Response**: Return processing results to TeleAIAgent

## Metadata Structure

### Telegram Metadata (Input)
```json
{
  "chat_id": -1001234567890,
  "chat_title": "My Group Chat",
  "chat_type": "supergroup", 
  "user_id": 123456789,
  "user_name": "Alice",
  "message_id": 12345,
  "timestamp": "2025-09-19 10:30:00",
  "date": "2025-09-19",
  "file_id": "AgACAgIAAx0...",
  "file_size": 156789,
  "has_caption": true,
  "caption": "Beautiful sunset photo"
}
```

### Qdrant Storage (Enhanced)
```json
{
  "chat_id": "-1001234567890",
  "chat_title": "My Group Chat", 
  "chat_type": "supergroup",
  "user_id": "123456789",
  "user_name": "Alice",
  "message_id": "12345",
  "timestamp": "2025-09-19 10:30:00",
  "date": "2025-09-19",
  "file_id": "AgACAgIAAx0...",
  "file_path": "/app/volume_images/2025/09/19/chat_-1001234567890_msg_12345_AgACAgIAAx0.jpg",
  "file_size": 156789,
  "description": "1. Anime-style woman with pink hair wearing red outfit. 2. Standing in cozy living room with white couch. 3. Bright cheerful atmosphere with warm lighting.",
  "processed_at": "2025-09-19 10:30:15",
  "service": "vision",
  "document_type": "image_analysis",
  "analysis_model": "llama3.2-vision:11b"
}
```

## File Organization

```
/app/volume_images/
├── 2025/
│   ├── 09/
│   │   ├── 19/
│   │   │   ├── chat_-1001234567890_msg_12345_AgACAgIAAx0.jpg
│   │   │   ├── chat_-1001234567890_msg_12346_BgBCBgIAAx0.jpg
│   │   │   └── ...
│   │   ├── 20/
│   │   └── ...
│   ├── 10/
│   └── ...
└── ...
```

## Dependencies

### Core Dependencies
- **FastAPI 0.104.1**: Modern web framework
- **uvicorn 0.24.0**: ASGI server
- **aiohttp 3.10.10**: Async HTTP client
- **Pillow 10.0.1**: Image processing

### AI/ML Stack
- **PyTorch 2.4.0+cpu**: CPU-optimized ML framework
- **sentence-transformers 3.0.1**: Semantic embeddings
- **qdrant-client 1.11.0**: Vector database client

### Integration
- **httpx 0.25.2**: Ollama HTTP client
- **python-multipart 0.0.6**: File upload support
- **structlog 23.2.0**: Structured logging

## Deployment

### Docker Build
```bash
# Build vision service
docker compose build vision

# Start all services
docker compose up -d

# Check vision logs
docker compose logs -f vision
```

### Health Monitoring
```bash
# Check service health
curl http://localhost:7777/health

# Get service statistics  
curl http://localhost:7777/stats

# Monitor processing logs
docker compose logs vision | grep "Image processing"
```

### Resource Requirements
- **CPU**: 2+ cores recommended for AI processing
- **Memory**: 3GB limit (1GB reservation) for models + processing
- **Storage**: Scales with image volume (10GB+ recommended)
- **Network**: Internal Docker networking to ollama and qdrant

## Integration with TeleAIAgent

The vision service is automatically integrated:

1. **TeleAIAgent Change**: Modified `file_handler.py` to forward images instead of direct storage
2. **VisionClient**: New client in `teleaiagent/utils/vision_client.py` 
3. **Async Integration**: Proper async/await patterns for non-blocking operation
4. **Error Handling**: Graceful degradation if vision service unavailable

### Original vs New Flow

**Before (Direct Storage):**
```
Telegram → TeleAIAgent → Local File Storage
```

**After (Microservice):**
```
Telegram → TeleAIAgent → Vision Service → Ollama Analysis → Qdrant + File Storage
```

## Testing

### Integration Test
```bash
# Run comprehensive integration test
python test_vision_integration.py
```

### Manual Testing
```bash
# Health check
curl http://localhost:7777/health

# Upload test image
curl -X POST http://localhost:7777/analyze-image \
  -F "image=@test_image.jpg" \
  -F 'telegram_metadata={"chat_id": 12345, "user_name": "Test"}'
```

## Troubleshooting

### Common Issues

**Service Not Starting:**
```bash
# Check all dependencies are running
docker compose ps

# Check vision logs
docker compose logs vision

# Verify Ollama model availability
docker compose exec ollama ollama list
```

**Processing Errors:**
```bash
# Check Ollama connection
curl http://localhost:11434/api/version

# Check Qdrant connection
curl http://localhost:6333/collections

# Test with smaller image
curl -X POST http://localhost:7777/analyze-image -F "image=@small_test.jpg" -F 'telegram_metadata={}'
```

**Performance Issues:**
```bash
# Monitor resource usage
docker stats vision

# Check processing times in logs
docker compose logs vision | grep "Duration"

# Consider using smaller Ollama model
# Edit vision/config.py: OLLAMA_MODEL = "llava:7b"
```

## Future Enhancements

### Planned Features
- **Batch Processing**: Multiple image processing in single request
- **Image Similarity Search**: Direct image-to-image comparison
- **Advanced Filtering**: Date range, user, chat filters for search
- **Caching**: Redis integration for frequently accessed data
- **Thumbnails**: Automatic thumbnail generation for quick preview

### Scaling Considerations
- **Horizontal Scaling**: Multiple vision service instances
- **Load Balancing**: Nginx or similar for request distribution  
- **Queue System**: Redis/RabbitMQ for asynchronous processing
- **Database Sharding**: Multiple Qdrant collections for large deployments

---

The Vision microservice provides a robust, scalable solution for AI-powered image analysis and semantic storage, seamlessly integrating with the existing TeleAIAgent architecture while maintaining high performance and reliability.