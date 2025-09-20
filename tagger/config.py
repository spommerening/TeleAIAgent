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
    # OLLAMA_MODEL = "gemma3n:e2b"  # Same as teleaiagent
    # OLLAMA_MODEL = "llava:7b"  # Better vision model
    OLLAMA_MODEL = "llava-llama3:8b-v1.1-q4_0"  # Better vision model with Llama 3
    # OLLAMA_MODEL = "llava-llama3:13b-v1.1-q4_0"  # Uncomment for better results, requires more RAM
    OLLAMA_TEMPERATURE = 0.7
    
    # Qdrant configuration (inherited from teleaiagent)
    QDRANT_HOST = "qdrant"
    QDRANT_PORT = 6333
    QDRANT_COLLECTION_NAME = "image_tags"  # Separate collection for image tags
    
    # Embedding model for semantic search
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # CPU-optimized sentence transformer
    
    # Enhanced image tagging configuration
    IMAGE_TAGGING_PROMPT = """
Du bist ein Experte für Bildanalyse. Analysiere dieses Bild sehr detailliert und erstelle hochwertige, beschreibende Tags in deutscher Sprache.

ANALYSIERE diese Bereiche systematisch:
🎯 HAUPTOBJEKTE: Was sind die Hauptelemente im Bild? (Personen, Tiere, Gegenstände)
🎨 VISUELLE EIGENSCHAFTEN: Farben, Beleuchtung, Komposition, Stil, Qualität
🌍 KONTEXT & SETTING: Wo spielt sich die Szene ab? (Innen/Außen, Tageszeit, Ort)
💭 STIMMUNG & ATMOSPHÄRE: Welche Gefühle vermittelt das Bild?
🎬 AKTIVITÄTEN & HANDLUNGEN: Was passiert im Bild?
📸 TECHNISCHE ASPEKTE: Perspektive, Bildqualität, Aufnahmewinkel

QUALITÄTSREGELN für Tags:
- Sei spezifisch statt allgemein (z.B. "goldstündlicht" statt "licht")
- Nutze beschreibende Adjektive (z.B. "flauschige-katze" statt "katze")
- Erfasse Emotionen und Stimmung (z.B. "gemütlich", "melancholisch")
- Beschreibe Farbnuancen (z.B. "warmes-orange", "kühles-blau")
- Erfasse den Stil (z.B. "retro", "modern", "künstlerisch")

BEISPIELE guter Tags:
- Für eine Katze am Fenster: "entspannte-katze, warmes-sonnenlicht, gemütliche-wohnatmosphäre, nachmittagsstimmung, häusliche-geborgenheit"
- Für eine Landschaft: "weitläufige-berglandschaft, dramatische-wolkenformation, goldene-stunde, erhabene-natur, panoramablick"

Erstelle 8-12 präzise, beschreibende Tags als kommagetrennte Liste. Keine Erklärungen, nur die Tags.
    """
    
    # Alternative prompts for multi-pass analysis
    ARTISTIC_ANALYSIS_PROMPT = """
Analysiere dieses Bild aus künstlerischer Sicht. Fokussiere auf:
- Komposition und Bildaufbau
- Farbharmonie und Beleuchtung  
- Stil und Ästhetik
- Künstlerische Techniken
- Emotionale Wirkung

Erstelle 5-7 Tags die diese künstlerischen Aspekte in deutscher Sprache beschreiben.
Nur Tags als kommagetrennte Liste, keine Erklärungen.
    """
    
    CONTEXTUAL_ANALYSIS_PROMPT = """
Analysiere den Kontext und die Geschichte dieses Bildes:
- Zeitlicher Kontext (Tageszeit, Jahreszeit, Epoche)
- Sozialer/kultureller Kontext
- Geografischer Kontext
- Situativer Kontext (Was passiert hier?)
- Zweck/Intention des Bildes

Erstelle 5-7 kontextuelle Tags in deutscher Sprache als kommagetrennte Liste.
    """
    
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
    
    # Tag Quality Configuration
    MIN_TAG_LENGTH = 3
    MAX_TAG_LENGTH = 50
    MIN_TAGS_COUNT = 5
    MAX_TAGS_COUNT = 15
    
    # Generic tags to filter out (too common/not descriptive)
    FILTER_GENERIC_TAGS = [
        "bild", "foto", "image", "picture", "aufnahme", "digital", "farbe", "farbig",
        "sichtbar", "erkennbar", "zeigt", "darstellung", "abbildung", "zu-sehen",
        "vorhanden", "existiert", "da", "hier", "dort", "gut", "schön", "normal"
    ]
    
    # Tag categories for better organization
    TAG_CATEGORIES = {
        "objects": ["person", "tier", "gebäude", "fahrzeug", "möbel", "pflanze", "essen", "kleidung"],
        "colors": ["rot", "blau", "grün", "gelb", "orange", "lila", "rosa", "schwarz", "weiß", "grau", "braun"],
        "moods": ["fröhlich", "traurig", "friedlich", "aufregend", "gemütlich", "dramatisch", "romantisch", "melancholisch"],
        "settings": ["innen", "außen", "natur", "stadt", "haus", "büro", "strand", "wald", "berg", "wasser"],
        "actions": ["laufen", "sitzen", "stehen", "spielen", "arbeiten", "schlafen", "essen", "lächeln", "schauen"],
        "technical": ["nahaufnahme", "weitwinkel", "portrait", "landschaft", "makro", "lowlight", "gegenlicht", "bokeh"],
        "time": ["morgen", "mittag", "abend", "nacht", "sommer", "winter", "frühling", "herbst", "goldstunde"],
        "style": ["vintage", "modern", "klassisch", "künstlerisch", "minimalistisch", "abstrakt", "realistisch"]
    }
    
    # Enhanced model configuration
    PRIMARY_VISION_MODEL = "llava:7b"  # Better vision model
    FALLBACK_VISION_MODEL = "gemma3n:e2b"  # Fallback if primary not available
    
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