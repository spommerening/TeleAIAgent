# Copilot Instructions for TeleAIAgent

## Project Overview
TeleAIAgent is a microservices-based AsyncIO Telegram bot with AI-powered image tagging and semantic search. It consists of 4 Docker services: `teleaiagent` (main bot), `tagger` (image analysis), `qdrant` (vector DB), and `ollama` (local LLM).

## Architecture Principles

### AsyncIO-First Design
- **All I/O operations use `async`/`await`**: File operations use `aiofiles`, HTTP calls use `aiohttp`
- **Concurrent processing**: Multiple users can interact simultaneously without blocking
- **aiogram 3.x patterns**: Event-driven handlers with dependency injection
- **Resource management**: Use `@asynccontextmanager` for service lifecycle (see `tagger/main.py`)

### Microservice Communication
- **Tagger service**: FastAPI on port 7777, called via `TaggerClient` with `aiohttp`
- **Qdrant integration**: Both services use `QdrantManager` for vector operations
- **Shared volumes**: Images stored in `/volumes/images` with year/month/day structure
- **Service dependencies**: `teleaiagent` depends on `tagger`, `tagger` depends on `qdrant` and `ollama`

### Configuration Management
- **Central config classes**: `teleaiagent/config.py` and `tagger/config.py`
- **Environment-driven**: All secrets and URLs from `.env` file
- **Docker service names**: Use container names for internal URLs (`ollama:11434`, `qdrant:6333`)
- **CPU-only optimization**: PyTorch configured for CPU-only execution

## Key Development Patterns

### Error Handling & Logging
```python
# Pattern: Structured logging with context
logger = logging.getLogger(__name__)
logger.info("🔄 Processing image with metadata: %s", metadata)

# Pattern: Graceful degradation
try:
    result = await some_ai_operation()
except Exception as e:
    logger.error("AI operation failed: %s", e)
    return {"status": "error", "fallback": True}
```

### Vector Database Operations
- **Qdrant collections**: Use `chat_context` for conversations, separate collections for images
- **384D embeddings**: SentenceTransformers with `all-MiniLM-L6-v2` model
- **Similarity threshold**: Default 0.3 for relevance filtering
- **Async operations**: All Qdrant calls are async with proper connection management

### File Management
- **Organized storage**: `FileManager` creates `YYYY/MM/DD` directory structures
- **Unique filenames**: UUID-based naming to prevent conflicts
- **Metadata preservation**: Store Telegram context alongside files
- **Volume mounting**: Use `/app/volume_images` in tagger, `/app/images` in teleaiagent

### Testing Approach
- **Integration tests**: `test_tagger_integration.py` for end-to-end workflows
- **Component tests**: `test_qdrant.py`, `test_async.py` for specific features
- **Manual testing**: Use `curl` commands for tagger API endpoints
- **Health checks**: `/health` endpoint with Docker health monitoring

## Development Workflows

### Local Python Environment
- **Virtual Environment**: Use `./venv` (not committed to repo)
- **Activation Required**: Always run `source ./venv/bin/activate` before Python scripts
- **Testing from Host**: Integration tests must run from activated venv

### Docker Commands (Modern Syntax)
```bash
# Build and start all services
docker compose up --build -d

# View logs for specific service
docker compose logs -f teleaiagent
docker compose logs -f tagger

# Test services individually (from container)
docker compose exec teleaiagent python test_async.py

# Test from host (requires venv activation)
source ./venv/bin/activate
python test_tagger_integration.py
```

### Service Dependencies
1. **Start order**: `qdrant` → `ollama` → `tagger` → `teleaiagent`
2. **Health checks**: Tagger has built-in health monitoring, teleaiagent has manual tests
3. **Model management**: Ollama models are pulled on first use (e.g., `gemma3n:e2b` for vision)
4. **CPU Performance**: First model downloads and inference can take 5-15+ minutes on CPU-only systems

### Debugging Strategies
- **Enable HTTP debugging**: Set `DEBUG_HTTP_LIBRARIES=True` in config
- **Service isolation**: Test tagger API independently with curl before bot integration
- **Vector search debugging**: Use similarity scores and result counts to tune retrieval
- **AsyncIO monitoring**: Check concurrent task counts and performance metrics
- **CPU Performance Issues**: Expect long waits (5-15+ min) for AI operations, use extended timeouts

## Critical Files & Their Purpose

### Core Bot Logic
- `teleaiagent/main.py`: AsyncIO bot initialization and signal handling
- `teleaiagent/handlers/`: Message processing with concurrent support
- `teleaiagent/utils/context_manager.py`: Qdrant RAG implementation
- `teleaiagent/utils/ai_client.py`: Multi-backend AI client (Perplexity/Ollama)

### Tagger Microservice
- `tagger/main.py`: FastAPI service with lifespan management
- `tagger/handlers/image_handler.py`: Complete image processing workflow
- `tagger/utils/ollama_client.py`: Vision AI client for image analysis
- `tagger/utils/tag_processor.py`: Tag extraction and formatting

### Infrastructure
- `docker-compose.yml`: Service orchestration with resource limits
- `Dockerfile-*`: CPU-optimized containers with PyTorch CPU-only
- `volumes/`: Persistent data with organized directory structures

## Common Pitfalls to Avoid

1. **GPU dependencies**: Always use CPU-only PyTorch (`torch+cpu` index)
2. **Blocking operations**: Never use sync I/O in async contexts
3. **Service URLs**: Use Docker service names, not localhost
4. **Resource limits**: Respect memory limits in docker-compose (2GB teleaiagent, 3GB tagger)
5. **Vector dimensions**: Ensure consistent 384D embeddings across services
6. **Error propagation**: Handle microservice failures gracefully with fallbacks
7. **Python environment**: Always activate `./venv` before running Python scripts from host
8. **CPU timeouts**: Set generous timeouts (600s+) for AI operations, first runs take 15+ minutes

## Environment Variables Required
```bash
TG_BOT_TOKEN="telegram_bot_token"
PERPLEXITY_API_KEY="perplexity_api_key"  # If using Perplexity
AI_BACKEND="perplexity"  # or "ollama"
DEBUG_HTTP_LIBRARIES=false  # Set true for debugging
```

When working on this codebase, prioritize AsyncIO patterns, maintain service boundaries, and ensure all AI operations have proper error handling and logging.