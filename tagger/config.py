"""
Configuration Settings for Tagger Microservice
"""

import os
from datetime import datetime

class Config:
    """Central configuration class for tagger service"""
    
    # Service configuration
    SERVICE_NAME = "tagger"
    SERVICE_HOST = "0.0.0.0"
    SERVICE_PORT = 7777
    
    # Ollama configuration
    OLLAMA_URL = "http://ollama:11434"
    OLLAMA_API_URL = "http://ollama:11434/api/chat"
    OLLAMA_TEMPERATURE = 0.7
    
    # Timeout configuration for CPU-only systems (30 minutes for inference)
    OLLAMA_INFERENCE_TIMEOUT = 1800  # 30 minutes for CPU vision model inference
    OLLAMA_DOWNLOAD_TIMEOUT = 1800   # 30 minutes for model downloads  
    OLLAMA_HEALTH_TIMEOUT = 10       # 10 seconds for health checks
    OLLAMA_HEALTH_INTERVAL = 60      # Health check every 60 seconds during inference
    
    # Qdrant configuration (inherited from teleaiagent)
    QDRANT_HOST = "qdrant"
    QDRANT_PORT = 6333
    QDRANT_COLLECTION_NAME = "image_tags"  # Separate collection for image tags
    
    # Embedding model for semantic search
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # CPU-optimized sentence transformer
    
    # File storage configuration
    IMAGES_BASE_DIR = "/app/images"
    IMAGES_VOLUME_DIR = "/app/volume_images"  # Mapped to docker volume
    
    # Logging configuration
    LOGS_DIR = "/app/logs"
    LOG_LEVEL = "INFO"
    DEBUG_HTTP_LIBRARIES = False  # Control httpx, aiohttp and other HTTP libraries logging (False = WARNING level)
    
    # Processing limits
    MAX_IMAGE_SIZE_MB = 10
    SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp", "gif"]
    
    # Vision model configuration (ordered by preference)
    # The system will try models in this order until one is available
    VISION_MODELS = [
        "llava-llama3:8b-v1.1-q4_0",  # Primary: Best quality, German support, ~5.5GB RAM
        "llava:7b",                    # Fallback: Good quality, standard model, ~4GB RAM  
        "gemma3n:e2b"                  # Emergency: Basic vision, minimal resources, ~2GB RAM
    ]
    
    @classmethod
    def get_vision_model_config(cls):
        """
        Get vision model configuration with intelligent fallback chain
        
        Strategy:
        1. Try primary model (best quality & features)
        2. Fallback to standard model (good compatibility)  
        3. Emergency fallback (minimal resources)
        4. If none available, attempt to pull primary model
        
        Returns:
            Dict with model hierarchy for OllamaClient
        """
        return {
            'primary_model': cls.VISION_MODELS[0],      # Best: llava-llama3:8b-v1.1-q4_0
            'fallback_model': cls.VISION_MODELS[1],     # Good: llava:7b
            'emergency_fallback': cls.VISION_MODELS[2]  # Basic: gemma3n:e2b
        }
    
    # Create directories
    DIRECTORIES = [LOGS_DIR, IMAGES_BASE_DIR, IMAGES_VOLUME_DIR]
    
    @classmethod
    def create_directories(cls):
        """Creates all required directories"""
        for directory in cls.DIRECTORIES:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def get_image_path(cls, telegram_metadata: dict) -> str:
        """
        Generate image path with year/month/day structure
        
        Args:
            telegram_metadata: Metadata from Telegram message
            
        Returns:
            Full path where image should be stored
        """
        now = datetime.now()
        year_month_day = now.strftime("%Y/%m/%d")
        
        # Create filename from message metadata
        chat_id = telegram_metadata.get('chat_id', 'unknown')
        message_id = telegram_metadata.get('message_id', 'unknown')
        file_id = telegram_metadata.get('file_id', 'unknown')
        
        filename = f"chat_{chat_id}_msg_{message_id}_{file_id}.jpg"
        
        return os.path.join(cls.IMAGES_VOLUME_DIR, year_month_day, filename)

# Create directories on import
Config.create_directories()