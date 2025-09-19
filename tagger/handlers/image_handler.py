"""
Image Handler for Tagger Service
Coordinates image processing workflow: analysis, tagging, storage, and Qdrant indexing
"""

import json
import time
from typing import Dict, List

import logging
from fastapi import HTTPException

from utils.ollama_client import OllamaClient
from utils.file_manager import FileManager
from utils.qdrant_client import QdrantManager
from utils.tag_processor import TagProcessor

logger = logging.getLogger(__name__)


class ImageHandler:
    """Handles complete image processing workflow"""
    
    def __init__(self, ollama_client: OllamaClient, file_manager: FileManager, qdrant_manager: QdrantManager):
        """Initialize image handler with required clients"""
        self.ollama_client = ollama_client
        self.file_manager = file_manager
        self.qdrant_manager = qdrant_manager
        self.tag_processor = TagProcessor()
        logger.info("🎯 Enhanced Image Handler initialized with advanced tag processing")
    
    async def process_image(self, 
                          image_data: bytes, 
                          telegram_metadata: str,
                          filename: str = None) -> Dict:
        """
        Process an image through the complete workflow
        
        Args:
            image_data: Raw image bytes
            telegram_metadata: JSON string with Telegram message metadata
            filename: Optional original filename
            
        Returns:
            Dict with processing results including document_id and storage_path
        """
        try:
            # Parse telegram metadata
            try:
                metadata = json.loads(telegram_metadata) if isinstance(telegram_metadata, str) else telegram_metadata
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in telegram_metadata: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid telegram_metadata JSON")
            
            logger.info(f"🚀 Starting complete image processing workflow, chat_id={metadata.get('chat_id')}, user_name={metadata.get('user_name')}, message_id={metadata.get('message_id')}")
            
            # Step 1: Enhanced multi-pass image analysis
            logger.info("🤖 Step 1: Enhanced multi-pass image analysis with Ollama...")
            
            # Perform multi-pass analysis for better tag quality
            analysis_results = await self.ollama_client.analyze_image_multi_pass(image_data)
            
            # Process and enhance tags with quality filtering
            tag_processing_result = self.tag_processor.merge_multi_pass_tags(
                primary_result=self.tag_processor.process_tags(analysis_results['primary_tags']),
                artistic_tags=analysis_results.get('artistic_tags', []),
                contextual_tags=analysis_results.get('contextual_tags', [])
            )
            
            tags = tag_processing_result['tags']
            tag_metadata = {
                'quality_score': tag_processing_result['quality_score'],
                'categorized_tags': tag_processing_result.get('categorized_tags', {}),
                'multi_pass_info': tag_processing_result.get('sources', {}),
                'model_used': analysis_results.get('model_used', 'unknown')
            }
            
            logger.info(f"✅ Enhanced analysis completed: {len(tags)} high-quality tags (quality: {tag_processing_result['quality_score']})")
            
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
            
            # Step 4: Create comprehensive metadata with enhanced tagging information
            enhanced_metadata = {
                **metadata,
                'tags': tags,
                'image_path': stored_path,
                'storage_path': storage_path,
                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'tag_count': len(tags),
                'tagging_metadata': tag_metadata,
                'enhanced_tagging': True
            }
            
            # Step 5: Store in Qdrant for semantic search
            logger.info("🗄️ Step 5: Storing tags in Qdrant...")
            doc_id = await self.qdrant_manager.store_image_tags(
                tags=tags,
                image_path=stored_path,
                metadata=enhanced_metadata
            )
            logger.info(f"✅ Tags stored in Qdrant, document_id={doc_id}")
            
            # Return comprehensive result with enhanced tagging information
            result = {
                'success': True,
                'document_id': doc_id,
                'storage_path': stored_path,
                'tags': tags,
                'tag_count': len(tags),
                'metadata': enhanced_metadata,
                'tag_quality': tag_metadata['quality_score'],
                'categorized_tags': tag_metadata['categorized_tags'],
                'model_info': {
                    'model_used': tag_metadata['model_used'],
                    'multi_pass': tag_metadata.get('multi_pass_info', {})
                }
            }
            
            logger.info("🎉 Complete image processing workflow finished successfully")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in telegram_metadata: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid telegram_metadata: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Image processing workflow failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
    
    async def search_similar_images(self, query_text: str, limit: int = 10) -> List[Dict]:
        """
        Search for images with similar content using semantic search
        
        Args:
            query_text: Text query to search for
            limit: Maximum number of results to return
            
        Returns:
            List of similar images with metadata and similarity scores
        """
        try:
            logger.info(f"🔍 Searching for similar images: '{query_text}' (limit={limit})")
            
            results = await self.qdrant_manager.search_similar_images(
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