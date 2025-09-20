"""
Image Handler for Tagger Service
Coordinates image processing workflow: analysis, description generation, storage, and Qdrant indexing
"""

import json
import time
from typing import Dict, List

import logging
from fastapi import HTTPException

from utils.ollama_client import OllamaClient
from utils.file_manager import FileManager
from utils.qdrant_client import QdrantManager
from utils.description_processor import DescriptionProcessor

logger = logging.getLogger(__name__)


class ImageHandler:
    """Handles complete image processing workflow with description generation"""
    
    def __init__(self, ollama_client: OllamaClient, file_manager: FileManager, qdrant_manager: QdrantManager):
        """Initialize image handler with required clients"""
        self.ollama_client = ollama_client
        self.file_manager = file_manager
        self.qdrant_manager = qdrant_manager
        self.description_processor = DescriptionProcessor()
        logger.info("🎯 Image Handler initialized for description generation")
    
    async def process_image(self, 
                          image_data: bytes, 
                          telegram_metadata: str,
                          filename: str = None) -> Dict:
        """
        Process an image through the simplified workflow with description generation
        
        Args:
            image_data: Raw image bytes
            telegram_metadata: JSON string with Telegram message metadata
            filename: Optional original filename
            
        Returns:
            Dict with processing results including document_id, storage_path, and description
        """
        try:
            # Parse telegram metadata
            try:
                metadata = json.loads(telegram_metadata) if isinstance(telegram_metadata, str) else telegram_metadata
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in telegram_metadata: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid telegram_metadata JSON")
            
            logger.info(f"🚀 Starting image description workflow, chat_id={metadata.get('chat_id')}, user_name={metadata.get('user_name')}, message_id={metadata.get('message_id')}")
            
            # Step 1: Generate comprehensive image description
            logger.info("🤖 Step 1: Generating image description with Ollama...")
            
            # Generate single comprehensive description
            description_result = await self.ollama_client.generate_image_description(image_data)
            raw_description = description_result['description']
            
            # Process and validate description
            processed_description = self.description_processor.process_description(raw_description)
            
            if not processed_description['is_valid']:
                logger.warning("⚠️ Generated description failed validation, using raw description")
                final_description = raw_description
                quality_score = 0.5
            else:
                final_description = processed_description['description']
                quality_score = processed_description['processing_stats']['quality_score']
            
            logger.info(f"✅ Description generated: {final_description[:100]}... (quality: {quality_score})")
            
            # Step 2: Generate storage path with year/month/day structure
            logger.info("📁 Step 2: Generating storage path...")
            storage_path = self.file_manager.get_image_storage_path(metadata)
            logger.info(f"✅ Storage path generated, path={storage_path}")
            
            # Step 3: Store image to filesystem
            logger.info("💾 Step 3: Storing image to filesystem...")
            stored_path = await self.file_manager.store_image(
                image_data=image_data,
                file_path=storage_path  # storage_path is already the full path including filename
            )
            
            # Step 4: Create comprehensive metadata with description information
            enhanced_metadata = {
                **metadata,
                'description': final_description,
                'image_path': stored_path,
                'storage_path': storage_path,
                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'description_length': len(final_description),
                'description_metadata': {
                    'quality_score': quality_score,
                    'model_used': description_result.get('model_used', 'unknown'),
                    'analysis_type': description_result.get('analysis_type', 'description'),
                    'is_valid': processed_description.get('is_valid', False)
                }
            }
            
            # Step 5: Store in Qdrant for semantic search
            logger.info("🗄️ Step 5: Storing description in Qdrant...")
            doc_id = await self.qdrant_manager.store_image_description(
                description=final_description,
                image_path=stored_path,
                metadata=enhanced_metadata
            )
            logger.info(f"✅ Description stored in Qdrant, document_id={doc_id}")
            
            # Return comprehensive result with description information
            result = {
                'success': True,
                'document_id': doc_id,
                'storage_path': stored_path,
                'description': final_description,
                'description_length': len(final_description),
                'metadata': enhanced_metadata,
                'quality_score': quality_score,
                'model_info': {
                    'model_used': description_result.get('model_used', 'unknown'),
                    'analysis_type': description_result.get('analysis_type', 'description')
                }
            }
            
            logger.info("🎉 Image description workflow finished successfully")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in telegram_metadata: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid telegram_metadata: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Image processing workflow failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
    
    async def search_similar_images(self, query_text: str, limit: int = 10) -> List[Dict]:
        """
        Search for images with similar descriptions using semantic search
        
        Args:
            query_text: Text query to search for
            limit: Maximum number of results to return
            
        Returns:
            List of similar images with metadata and similarity scores
        """
        try:
            logger.info(f"🔍 Searching for similar images by description: '{query_text}' (limit={limit})")
            
            results = await self.qdrant_manager.search_similar_descriptions(
                query_text=query_text,
                limit=limit
            )
            
            logger.info(f"✅ Found {len(results)} similar images")
            return results
            
        except Exception as e:
            logger.error(f"❌ Similar images search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    async def get_processing_stats(self) -> Dict:
        """
        Get comprehensive statistics about image processing
        
        Returns:
            Dict with processing statistics
        """
        try:
            logger.info("📊 Gathering processing statistics...")
            
            # Get stats from different components
            qdrant_stats = await self.qdrant_manager.get_stats()
            storage_stats = self.file_manager.get_storage_stats()
            
            # Combine stats
            stats = {
                'qdrant': qdrant_stats,
                'storage': storage_stats,
                'service_status': 'healthy'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get processing stats: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Stats gathering failed: {str(e)}")