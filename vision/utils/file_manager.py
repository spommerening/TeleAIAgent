"""
File Manager for Vision Service
Handles file system operations including year/month/day directory structure
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from config import Config

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file system operations for image storage"""
    
    def __init__(self):
        self.base_dir = Path(Config.IMAGES_VOLUME_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def get_image_storage_path(self, telegram_metadata: Dict) -> str:
        """
        Generate image storage path with year/month/day structure
        
        Args:
            telegram_metadata: Metadata from Telegram message
            
        Returns:
            Full path where image should be stored
        """
        # Extract date information
        timestamp = telegram_metadata.get('timestamp')
        if timestamp:
            try:
                # Parse timestamp to get date components
                if isinstance(timestamp, str):
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                else:
                    dt = timestamp
            except (ValueError, TypeError):
                dt = datetime.now()
        else:
            dt = datetime.now()
            
        # Create year/month/day structure
        year_month_day = dt.strftime("%Y/%m/%d")
        date_dir = self.base_dir / year_month_day
        
        # Ensure directory exists
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from message metadata
        chat_id = telegram_metadata.get('chat_id', 'unknown')
        message_id = telegram_metadata.get('message_id', 'unknown')
        file_id = telegram_metadata.get('file_id', 'unknown')
        
        # Create unique filename
        filename = f"chat_{chat_id}_msg_{message_id}_{file_id}.jpg"
        
        full_path = date_dir / filename
        
        logger.info(f"📁 Generated storage path - path: {str(full_path)}, date_structure: {year_month_day}, filename: {filename}")
        
        return str(full_path)
        
    async def store_image(self, image_data: bytes, file_path: str) -> Dict:
        """
        Store image data to filesystem
        
        Args:
            image_data: Raw image bytes
            file_path: Target file path
            
        Returns:
            Dictionary with storage information
        """
        logger.info(f"💾 Storing image to filesystem - path: {file_path}, size_bytes: {len(image_data)}")
        
        try:
            # Ensure parent directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write image data
            with open(file_path, 'wb') as f:
                f.write(image_data)
                
            # Get file info
            file_size = os.path.getsize(file_path)
            file_stats = os.stat(file_path)
            
            storage_info = {
                'file_path': file_path,
                'file_size': file_size,
                'stored_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'success': True
            }
            
            logger.info(f"✅ Image stored successfully - path: {file_path}, size_bytes: {file_size}")
            
            return storage_info
            
        except Exception as e:
            logger.error(f"❌ Failed to store image - path: {file_path}, error: {str(e)}")
            raise
            
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            directories = set()
            
            # Walk through all files
            for root, dirs, files in os.walk(self.base_dir):
                directories.add(root)
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            file_count += 1
                        except OSError:
                            continue
                            
            return {
                'base_directory': str(self.base_dir),
                'total_images': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'directory_count': len(directories),
                'directories': sorted([str(Path(d).relative_to(self.base_dir)) for d in directories if d != str(self.base_dir)])
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get storage stats: {str(e)}")
            return {
                'error': str(e),
                'base_directory': str(self.base_dir)
            }
            
    def cleanup_old_files(self, days_old: int = 30) -> Dict:
        """
        Clean up files older than specified days (optional maintenance function)
        
        Args:
            days_old: Delete files older than this many days
            
        Returns:
            Dictionary with cleanup results
        """
        logger.info(f"🧹 Starting file cleanup, days_old={days_old}")
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_files = []
            deleted_size = 0
            
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_stats = os.stat(file_path)
                        if file_stats.st_mtime < cutoff_time:
                            file_size = file_stats.st_size
                            os.remove(file_path)
                            deleted_files.append(file_path)
                            deleted_size += file_size
                            
                    except OSError:
                        continue
                        
            # Remove empty directories
            for root, dirs, files in os.walk(self.base_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            os.rmdir(dir_path)
                    except OSError:
                        continue
                        
            cleanup_result = {
                'deleted_files': len(deleted_files),
                'deleted_size_mb': round(deleted_size / (1024 * 1024), 2),
                'cutoff_days': days_old
            }
            
            logger.info(f"✅ File cleanup completed - {cleanup_result}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"❌ File cleanup failed: {str(e)}")
            return {'error': str(e)}
            
    def health_check(self) -> bool:
        """Check if file system is healthy"""
        try:
            # Check if base directory exists and is writable
            if not self.base_dir.exists():
                return False
                
            # Test write permissions by creating a temporary file
            test_file = self.base_dir / '.health_check'
            test_file.write_text('health_check')
            test_file.unlink()
            
            return True
            
        except Exception:
            return False
            
    def health_check(self) -> bool:
        """Check if file system is healthy"""
        try:
            # Check if base directories are accessible
            return (Path(Config.IMAGES_VOLUME_DIR).exists() and 
                   Path(Config.IMAGES_VOLUME_DIR).is_dir() and
                   os.access(Config.IMAGES_VOLUME_DIR, os.W_OK))
        except Exception:
            return False
    
    def get_stats(self) -> Dict:
        """Alias for get_storage_stats for consistency"""
        return self.get_storage_stats()