# Ollama Backend Setup Guide

This guide explains how to switch from the Perplexity AI backend to the local Ollama backend in TeleAIAgent, allowing you to run local Large Language Models (LLMs) without relying on external API services.

## 🎯 Overview

**Perplexity AI Backend:**
- ✅ Cloud-based, fast responses
- ✅ Integrated web search capabilities
- ❌ Requires API key and internet connection
- ❌ Usage costs and rate limits
- ❌ Data sent to external servers

**Ollama Backend:**
- ✅ Completely local and private
- ✅ No API costs or rate limits
- ✅ Works offline (after initial model download)
- ✅ Full control over model selection
- ❌ Requires more system resources
- ❌ No built-in web search
- ❌ Slower responses (hardware dependent)

## 🚀 Quick Setup

### Step 1: Update Environment Configuration
Edit your `.env` file:

```bash
# Change from Perplexity to Ollama
AI_BACKEND=ollama

# Perplexity API key is no longer needed (but can be kept for future use)
# PERPLEXITY_API_KEY=your_api_key

# Optional: Telegram bot token (still required)
TG_BOT_TOKEN=your_telegram_bot_token
```

### Step 2: Start Services
```bash
# Start all services including Ollama
docker compose up -d

# Check if Ollama is running
docker compose logs ollama
```

### Step 3: Verify Model Download
The bot will automatically download the default model (`gemma3n:e2b`) on first use. Monitor the download progress:

```bash
# Follow Ollama logs to see model download
docker compose logs -f ollama

# Or check teleaiagent logs for model initialization
docker compose logs -f teleaiagent
```

## 🔧 Detailed Configuration

### Available Models

You can change the default model in `src/config.py`:

```python
# Current default model
OLLAMA_MODEL = "gemma3n:e2b"  # ~2GB

# Popular alternatives:
# OLLAMA_MODEL = "llama3.2:3b"      # ~2GB, good balance
# OLLAMA_MODEL = "llama3.2:1b"      # ~1.3GB, faster, less capable
# OLLAMA_MODEL = "phi3:mini"        # ~2.3GB, Microsoft model
# OLLAMA_MODEL = "gemma2:2b"        # ~1.6GB, Google model
# OLLAMA_MODEL = "qwen2.5:1.5b"     # ~934MB, very fast
# OLLAMA_MODEL = "llama3.2"         # ~8GB, most capable (requires 8GB+ RAM)
```

### Model Management Commands

```bash
# List available models
docker compose exec ollama ollama list

# Pull a specific model manually
docker compose exec ollama ollama pull llama3.2:3b

# Remove a model to free space
docker compose exec ollama ollama rm old_model_name

# Check model information
docker compose exec ollama ollama show llama3.2:3b
```

## 📊 Performance Considerations

### System Requirements by Model Size

| Model | Size | RAM Needed | Speed | Quality |
|-------|------|------------|-------|---------|
| qwen2.5:1.5b | ~934MB | 2GB+ | Very Fast | Basic |
| llama3.2:1b | ~1.3GB | 3GB+ | Fast | Good |
| gemma2:2b | ~1.6GB | 4GB+ | Fast | Good |
| llama3.2:3b | ~2GB | 4GB+ | Medium | Very Good |
| phi3:mini | ~2.3GB | 4GB+ | Medium | Very Good |
| llama3.2 | ~8GB | 12GB+ | Slower | Excellent |

### Optimization Tips

1. **Choose the Right Model**: Start with smaller models (1-3B parameters) for testing
2. **Monitor Resources**: Use `docker stats` to monitor CPU and memory usage
3. **SSD Storage**: Store models on SSD for faster loading
4. **RAM**: Ensure sufficient RAM for model + OS + other containers

## 🔄 Switching Between Backends

### Switch to Ollama
```bash
# Update .env file
echo "AI_BACKEND=ollama" > .env.tmp
grep -v "^AI_BACKEND=" .env >> .env.tmp
mv .env.tmp .env

# Restart services
docker compose restart teleaiagent
```

### Switch Back to Perplexity
```bash
# Update .env file
echo "AI_BACKEND=perplexity" > .env.tmp
echo "PERPLEXITY_API_KEY=your_api_key" >> .env.tmp
grep -v "^AI_BACKEND=" .env | grep -v "^PERPLEXITY_API_KEY=" >> .env.tmp
mv .env.tmp .env

# Restart services
docker compose restart teleaiagent
```

### Dynamic Switching (Advanced)
You can implement backend switching through bot commands by modifying the configuration and restarting the AI client.

## 🐛 Troubleshooting

### Common Issues

**1. Model Download Fails**
```bash
# Check network connectivity
docker compose exec ollama ping google.com

# Check available disk space
docker compose exec ollama df -h

# Manually pull model with verbose output
docker compose exec ollama ollama pull llama3.2:3b --verbose
```

**2. Out of Memory Errors**
```bash
# Check available RAM
free -h

# Try a smaller model
docker compose exec ollama ollama pull qwen2.5:1.5b

# Update config.py to use smaller model
# OLLAMA_MODEL = "qwen2.5:1.5b"
```

**3. Slow Response Times**
```bash
# Check CPU usage
docker stats

# Consider using GPU acceleration (if available)
# Add to docker-compose.yml under ollama service:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

**4. Bot Not Responding**
```bash
# Check if backend is properly set
docker compose exec teleaiagent env | grep AI_BACKEND

# Check teleaiagent logs for errors
docker compose logs teleaiagent | grep -i error

# Verify Ollama is accessible from bot container
docker compose exec teleaiagent curl http://ollama:11434/api/version
```

### Log Analysis

```bash
# Monitor bot initialization
docker compose logs -f teleaiagent | grep -i "model\|ollama\|ai"

# Check Ollama service logs
docker compose logs ollama

# Monitor resource usage in real-time
docker stats --no-stream
```

## 🔧 Advanced Configuration

### Custom Model Configuration

Create a custom configuration by modifying `src/config.py`:

```python
class Config:
    # ... existing config ...
    
    # Custom Ollama settings
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
    OLLAMA_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', '0.7'))
    OLLAMA_TOP_P = float(os.getenv('OLLAMA_TOP_P', '0.9'))
    OLLAMA_TOP_K = int(os.getenv('OLLAMA_TOP_K', '40'))
```

Then set these in your `.env` file:
```bash
AI_BACKEND=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TEMPERATURE=0.5
OLLAMA_TOP_P=0.8
OLLAMA_TOP_K=20
```

### GPU Acceleration (NVIDIA)

If you have an NVIDIA GPU, add GPU support to docker-compose.yml:

```yaml
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-server
    volumes:
      - ./volumes/ollama:/root/.ollama
    networks:
      - mynetwork
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Multiple Models

You can configure multiple models for different purposes:

```python
# In config.py
OLLAMA_CHAT_MODEL = "llama3.2:3b"      # For conversations
OLLAMA_SUMMARY_MODEL = "qwen2.5:1.5b"  # For summarization
OLLAMA_CODE_MODEL = "deepseek-coder:6.7b"  # For coding tasks
```

## 📈 Performance Monitoring

### Resource Usage Monitoring

```bash
# Container resource usage
docker stats ollama-server teleaiagent

# System resources
htop

# Ollama-specific monitoring
docker compose exec ollama ollama ps
```

### Response Time Benchmarking

```bash
# Test response time
time docker compose exec ollama ollama run llama3.2:3b "Hello, how are you?"

# Monitor response times in bot logs
docker compose logs teleaiagent | grep "Processing time"
```

## 🔒 Security & Privacy Benefits

Using Ollama provides several privacy and security advantages:

✅ **Local Processing**: All conversations stay on your server  
✅ **No External Dependencies**: No internet required after model download  
✅ **No API Keys**: No risk of API key exposure  
✅ **Data Control**: Full control over conversation data  
✅ **Audit Trail**: Complete visibility into model behavior  

## 📚 Further Resources

- [Ollama Official Documentation](https://github.com/ollama/ollama)
- [Available Models Library](https://ollama.com/library)
- [Model Performance Comparisons](https://ollama.com/library)
- [GPU Setup Guide](https://github.com/ollama/ollama/blob/main/docs/gpu.md)

---

**Need Help?** Check the main [README.md](../README.md) for general troubleshooting or create an issue in the repository.