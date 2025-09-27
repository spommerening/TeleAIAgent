"""
Settings Manager for TeleAI Agent
Manages per-channel settings using SQLite with AsyncIO support
"""

import aiosqlite
import logging
import os
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ChannelSettings:
    """Data class for channel settings"""
    chat_id: int
    chat_title: str = ""
    chat_type: str = "private"
    vision_model: str = "llama3.2-vision:11b"
    text_model: str = "llama3.2:3b"
    auto_tag: bool = True
    response_language: str = "de"
    created_at: str = ""
    updated_at: str = ""


class SettingsManager:
    """Manages channel-specific settings using SQLite"""
    
    def __init__(self, db_path: str = "/app/data/settings.db"):
        self.db_path = db_path
        self._ensure_directory()
        logger.info(f"🔧 SettingsManager initialized with database: {db_path}")
    
    def _ensure_directory(self):
        """Ensure data directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"📁 Created settings directory: {db_dir}")
    
    async def initialize(self):
        """Initialize database and create tables if they don't exist"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Enable foreign keys and WAL mode for better concurrency
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute("PRAGMA journal_mode = WAL")
                
                # Create channel_settings table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS channel_settings (
                        chat_id INTEGER PRIMARY KEY,
                        chat_title TEXT NOT NULL DEFAULT '',
                        chat_type TEXT NOT NULL DEFAULT 'private',
                        vision_model TEXT NOT NULL DEFAULT 'llama3.2-vision:11b',
                        text_model TEXT NOT NULL DEFAULT 'llama3.2:3b',
                        auto_tag BOOLEAN NOT NULL DEFAULT true,
                        response_language TEXT NOT NULL DEFAULT 'de',
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create available_models table for reference
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS available_models (
                        model_name TEXT PRIMARY KEY,
                        model_type TEXT NOT NULL, -- 'vision' or 'text'
                        description TEXT DEFAULT '',
                        is_available BOOLEAN DEFAULT true,
                        last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert default models if they don't exist
                default_models = [
                    ("llama3.2-vision:11b", "vision", "Primary vision model - instruction-tuned image reasoning", True),
                    ("llava:7b", "vision", "Fallback vision model - good quality, standard", True),
                    ("llama3.2:3b", "text", "Primary text model - efficient and capable", True),
                    ("llama3.2:1b", "text", "Lightweight text model - fast responses", True),
                ]
                
                for model_name, model_type, description, is_available in default_models:
                    await db.execute("""
                        INSERT OR IGNORE INTO available_models 
                        (model_name, model_type, description, is_available) 
                        VALUES (?, ?, ?, ?)
                    """, (model_name, model_type, description, is_available))
                
                await db.commit()
                logger.info("✅ Settings database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize settings database: {e}", exc_info=True)
            raise
    
    async def get_channel_settings(self, chat_id: int) -> ChannelSettings:
        """Get all settings for a channel, create defaults if not exists"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM channel_settings WHERE chat_id = ?",
                    (chat_id,)
                )
                result = await cursor.fetchone()
                
                if result:
                    # Convert Row to dict and create ChannelSettings
                    settings_dict = dict(result)
                    return ChannelSettings(**settings_dict)
                else:
                    # Return defaults for new channel
                    logger.info(f"📝 No settings found for chat {chat_id}, returning defaults")
                    return ChannelSettings(chat_id=chat_id)
                    
        except Exception as e:
            logger.error(f"❌ Error getting channel settings for {chat_id}: {e}", exc_info=True)
            return ChannelSettings(chat_id=chat_id)  # Return defaults on error
    
    async def get_vision_model(self, chat_id: int) -> str:
        """Get vision model for channel (convenience method)"""
        settings = await self.get_channel_settings(chat_id)
        return settings.vision_model
    
    async def get_text_model(self, chat_id: int) -> str:
        """Get text model for channel (convenience method)"""
        settings = await self.get_channel_settings(chat_id)
        return settings.text_model
    
    async def set_channel_setting(self, chat_id: int, **kwargs) -> bool:
        """Update specific settings for a channel"""
        try:
            # Get current settings or defaults
            current_settings = await self.get_channel_settings(chat_id)
            
            # Update with new values
            for key, value in kwargs.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
                else:
                    logger.warning(f"⚠️ Unknown setting key: {key}")
            
            # Set timestamps
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            if not current_settings.created_at:
                current_settings.created_at = current_time
            current_settings.updated_at = current_time
            
            # Save to database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO channel_settings 
                    (chat_id, chat_title, chat_type, vision_model, text_model, 
                     auto_tag, response_language, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    current_settings.chat_id,
                    current_settings.chat_title,
                    current_settings.chat_type,
                    current_settings.vision_model,
                    current_settings.text_model,
                    current_settings.auto_tag,
                    current_settings.response_language,
                    current_settings.created_at,
                    current_settings.updated_at
                ))
                await db.commit()
            
            logger.info(f"✅ Updated settings for chat {chat_id}: {kwargs}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting channel settings for {chat_id}: {e}", exc_info=True)
            return False
    
    async def set_vision_model(self, chat_id: int, model: str, chat_title: str = None) -> bool:
        """Set vision model for channel (convenience method)"""
        update_data = {"vision_model": model}
        if chat_title:
            update_data["chat_title"] = chat_title
        return await self.set_channel_setting(chat_id, **update_data)
    
    async def set_text_model(self, chat_id: int, model: str, chat_title: str = None) -> bool:
        """Set text model for channel (convenience method)"""
        update_data = {"text_model": model}
        if chat_title:
            update_data["chat_title"] = chat_title
        return await self.set_channel_setting(chat_id, **update_data)
    
    async def get_available_models(self, model_type: str = None) -> List[Dict[str, Any]]:
        """Get list of available models, optionally filtered by type"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                if model_type:
                    cursor = await db.execute(
                        "SELECT * FROM available_models WHERE model_type = ? AND is_available = true ORDER BY model_name",
                        (model_type,)
                    )
                else:
                    cursor = await db.execute(
                        "SELECT * FROM available_models WHERE is_available = true ORDER BY model_type, model_name"
                    )
                
                results = await cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"❌ Error getting available models: {e}", exc_info=True)
            return []
    
    async def update_model_availability(self, model_name: str, is_available: bool) -> bool:
        """Update model availability status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE available_models 
                    SET is_available = ?, last_checked = CURRENT_TIMESTAMP 
                    WHERE model_name = ?
                """, (is_available, model_name))
                await db.commit()
                
                logger.info(f"✅ Updated model availability: {model_name} = {is_available}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error updating model availability: {e}", exc_info=True)
            return False
    
    async def get_channel_count(self) -> int:
        """Get total number of configured channels"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM channel_settings")
                result = await cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"❌ Error getting channel count: {e}", exc_info=True)
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Get channel count
                cursor = await db.execute("SELECT COUNT(*) as total FROM channel_settings")
                channel_count = (await cursor.fetchone())['total']
                
                # Get model usage statistics
                cursor = await db.execute("""
                    SELECT vision_model, COUNT(*) as count 
                    FROM channel_settings 
                    GROUP BY vision_model 
                    ORDER BY count DESC
                """)
                vision_models = [dict(row) for row in await cursor.fetchall()]
                
                cursor = await db.execute("""
                    SELECT text_model, COUNT(*) as count 
                    FROM channel_settings 
                    GROUP BY text_model 
                    ORDER BY count DESC
                """)
                text_models = [dict(row) for row in await cursor.fetchall()]
                
                return {
                    'total_channels': channel_count,
                    'vision_model_usage': vision_models,
                    'text_model_usage': text_models,
                    'database_path': self.db_path,
                    'database_exists': os.path.exists(self.db_path)
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}", exc_info=True)
            return {'error': str(e)}