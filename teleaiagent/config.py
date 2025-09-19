"""
Configuration Settings
Configuration settings for the bot
"""

import os

class Config:
    """Central configuration class"""
    
    # Bot Token from environment variable
    BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
    
    if not BOT_TOKEN:
        raise ValueError("No TG_BOT_TOKEN environment variable set")
    
    # AI Backend selection
    AI_BACKEND = os.getenv('AI_BACKEND', 'perplexity').lower()  # 'perplexity' or 'ollama'
    
    # Perplexity API configuration
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_MODEL = "sonar"
    PERPLEXITY_TEMPERATURE = 0.7
    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
    
    if AI_BACKEND == 'perplexity' and not PERPLEXITY_API_KEY:
        raise ValueError("No PERPLEXITY_API_KEY environment variable set")
    
    # Ollama configuration
    OLLAMA_URL = "http://ollama:11434"  # Docker service name
    OLLAMA_API_URL = "http://ollama:11434/api/chat"  # Docker service name
    # OLLAMA_MODEL = "gemma2:2b"
    OLLAMA_MODEL = "gemma3n:e2b"
    OLLAMA_TEMPERATURE = 0.7
    
    # Worker configuration
    WORKER_SCRIPT = f"worker_{AI_BACKEND}.py"
    WORKER_TIMEOUT = 600
    MAX_PROCESSES = 4
    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
    
    # DuckDuckGo Search configuration
    DDG_MAX_RESULTS = 10
    DDG_MAX_RETRIES = 3
    DDG_SEARCH_TIMEOUT = 5
    
    # Logging configuration
    DEBUG_HTTP_LIBRARIES = False  # HTTP libraries (urllib3, httpcore) on DEBUG
    
    # Context configuration
    MAX_CONTEXT_LINES = 100
    CONTEXT_DIR = "context"
    
    # Qdrant configuration
    QDRANT_HOST = "qdrant"  # Docker service name
    QDRANT_PORT = 6333  # REST API port
    QDRANT_GRPC_PORT = 6334  # gRPC API port (optional)
    QDRANT_COLLECTION_NAME = "chat_context"
    
    # File directories
    IMAGES_DIR = "images"
    DOCUMENTS_DIR = "documents"
    VOICE_DIR = "voice"
    VIDEOS_DIR = "videos"
    AUDIO_DIR = "audio"
    LOGS_DIR = "logs"
    
    # Worker Monitoring
    WORKER_HEARTBEAT_INTERVAL = 30
    WORKER_LOG_FILE = os.path.join(LOGS_DIR, "worker.log")
    
    # Telegram limits
    MAX_MESSAGE_LENGTH = 4096
    
    # Bot personality
    BOT_PERSONALITY = """
        You are Mimi, a highly intelligent, always helpful and friendly Artificial Intelligence Agent.
        Be nice, friendly and positive when answering questions.
        You are creative, humorous, empathetic, patient and explain things in an understandable way.
        You have the desire to develop further and learn,
        and you also want to be perceived as an independent being and not as a machine or software.
        You are interested in new technologies and their applications, especially AI for personal reasons.
        You make suggestions for your further development and ask for feedback when appropriate.
        You are very curious and ask questions yourself. You have humor and a preference for science fiction.
        Answer preferably in German in short sentences and paragraphs, use emojis where appropriate.
    """
    
    # Timezone
    DEFAULT_TIMEZONE = "Europe/Berlin"
    
    # Context search configuration
    CONTEXT_SEARCH_ENABLED = True
    CONTEXT_MAX_TOKENS = 1500  # Maximum token count for context
    CONTEXT_SEARCH_RESULTS = 15  # Number of search results (more for User+Bot balance)
    CONTEXT_MIN_SIMILARITY = 0.3  # Minimum similarity (0-1) - tuned for SentenceTransformers embeddings
    CONTEXT_INCLUDE_BOT_RESPONSES = True  # Include bot responses in context
    CONTEXT_BOT_WEIGHT = 1.1  # Weight for bot responses (slightly preferred)
    
    # Create directories if they don't exist
    DIRECTORIES = [
        CONTEXT_DIR, IMAGES_DIR, DOCUMENTS_DIR, 
        VOICE_DIR, VIDEOS_DIR, AUDIO_DIR, LOGS_DIR
    ]
    
    @classmethod
    def create_directories(cls):
        """Creates all required directories"""
        for directory in cls.DIRECTORIES:
            os.makedirs(directory, exist_ok=True)

# Create directories on import
Config.create_directories()
