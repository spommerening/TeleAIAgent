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
    
    # Ollama configuration (inherited from teleaiagent)
    OLLAMA_URL = "http://ollama:11434"
    OLLAMA_API_URL = "http://ollama:11434/api/chat"
    OLLAMA_MODEL = "gemma3n:e2b"  # Same as teleaiagent
    OLLAMA_TEMPERATURE = 0.7
    
    # Qdrant configuration (inherited from teleaiagent)
    QDRANT_HOST = "qdrant"
    QDRANT_PORT = 6333
    QDRANT_COLLECTION_NAME = "image_tags"  # Separate collection for image tags
    
    # Embedding model for semantic search
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # CPU-optimized sentence transformer
    
    # Image tagging configuration
    IMAGE_TAGGING_PROMPT = """
    Analyze this image and generate descriptive tags. 
    Provide 5-10 relevant tags that describe:
    1. Main objects/subjects in the image
    2. Colors, mood, and atmosphere
    3. Setting/location if identifiable
    4. Actions or activities shown
    5. Style or artistic elements
    
    Return only the tags as a comma-separated list, no explanations.
    Example: "person, outdoor, sunset, walking, peaceful, nature, golden light"
    """
    
    # File storage configuration
    IMAGES_BASE_DIR = "/app/images"
    IMAGES_VOLUME_DIR = "/app/volume_images"  # Mapped to docker volume
    
    # Logging configuration
    LOGS_DIR = "/app/logs"
    LOG_LEVEL = "INFO"
    
    # Processing limits
    MAX_IMAGE_SIZE_MB = 10
    SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp", "gif"]
    
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