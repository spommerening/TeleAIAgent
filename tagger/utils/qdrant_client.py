"""
Qdrant Client for Tagger Service
Handles vector database operations for storing image tags and metadata
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import torch

from config import Config

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manages Qdrant vector database operations for image tags and metadata"""
    
    def __init__(self):
        """Initialize Qdrant client and embedding model"""
        self.client = None
        self.embedding_model = None
        self.collection_name = Config.QDRANT_COLLECTION_NAME
        self.vector_size = 384  # all-MiniLM-L6-v2 embedding size
        
        # Force CPU usage for PyTorch
        torch.set_num_threads(1)
        
    async def initialize(self):
        """Initialize Qdrant client and embedding model"""
        try:
            # Initialize Qdrant client
            logger.info(f"🔧 Connecting to Qdrant at {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")
            self.client = QdrantClient(
                host=Config.QDRANT_HOST,
                port=Config.QDRANT_PORT,
            )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"✅ Connected to Qdrant, collections_count={len(collections.collections)}")
            
            # Initialize embedding model (CPU-optimized)
            logger.info("🔄 Loading SentenceTransformer model for embeddings...")
            
            # Force CPU usage
            device = 'cpu'
            logger.info(f"🖥️ Using device: {device}")
            
            self.embedding_model = SentenceTransformer(
                Config.EMBEDDING_MODEL_NAME,
                device=device
            )
            
            # Test embedding generation
            test_embedding = self.embedding_model.encode("test", convert_to_tensor=False)
            logger.info(f"✅ Embedding model loaded, vector_size={len(test_embedding)}")
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            logger.info("🎯 Qdrant Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant manager: {str(e)}")
            raise
    
    async def _ensure_collection_exists(self):
        """Ensure the required collection exists, create if not"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"✅ Collection already exists, collection={self.collection_name}")
            else:
                logger.info(f"🔄 Creating new collection, collection={self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE)
                )
                logger.info(f"✅ Collection created successfully, collection={self.collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure collection exists: {str(e)}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using SentenceTransformer"""
        try:
            # Combine multiple text sources for richer embeddings
            if isinstance(text, list):
                text = " ".join(text)
            
            # Generate embedding using CPU
            embedding = self.embedding_model.encode(
                text,
                convert_to_tensor=False,
                normalize_embeddings=True
            ).tolist()
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding, text={text[:100]}: {str(e)}")
            raise
    
    async def store_image_description(self, 
                                    description: str, 
                                    image_path: str, 
                                    metadata: Dict[str, Any]) -> str:
        """
        Store image description and metadata in Qdrant vector database
        
        Args:
            description: AI-generated image description
            image_path: Path to stored image file
            metadata: Complete metadata including Telegram info
            
        Returns:
            Document ID in Qdrant
        """
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Generate embedding from description
            embedding = self._generate_embedding(description)
            
            # Prepare payload with all metadata
            payload = {
                "description": description,
                "image_path": image_path,
                "stored_at": datetime.utcnow().isoformat(),
                "description_length": len(description),
                **metadata  # Include all Telegram metadata
            }
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"✅ Stored image description in Qdrant, doc_id={doc_id}, description_length={len(description)}")
            return doc_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store image description: {str(e)}")
            raise

    async def store_image_tags(self, 
                             tags: List[str], 
                             image_path: str, 
                             metadata: Dict[str, Any]) -> str:
        """
        Store image tags and metadata in Qdrant vector database (legacy method for compatibility)
        
        Args:
            tags: List of tags generated by AI
            image_path: Path to stored image file
            metadata: Complete metadata including Telegram info
            
        Returns:
            Document ID in Qdrant
        """
        # Convert tags to description for storage
        tags_as_description = ", ".join(tags) if tags else "No description available"
        return await self.store_image_description(tags_as_description, image_path, metadata)
    
    async def search_similar_descriptions(self, 
                                        query_text: str, 
                                        limit: int = 10,
                                        score_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search for images with similar descriptions using semantic search
        
        Args:
            query_text: Text query to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar images with metadata and scores
        """
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query_text)
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            # Format results
            results = []
            for result in search_results:
                result_dict = {
                    "id": result.id,
                    "score": result.score,
                    "description": result.payload.get("description", ""),
                    "image_path": result.payload.get("image_path"),
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["description", "image_path"]}
                }
                results.append(result_dict)
            
            logger.info(f"🔍 Found {len(results)} similar images for query: '{query_text}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Similar images search failed: {str(e)}")
            raise

    async def search_similar_images(self, 
                                  query_text: str, 
                                  limit: int = 10,
                                  score_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search for images with similar content using semantic search (legacy method)
        
        Args:
            query_text: Text query to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar images with metadata and scores
        """
        # Delegate to the new description search method
        return await self.search_similar_descriptions(query_text, limit, score_threshold)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Qdrant collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            
            # Get collection statistics
            stats = {
                "collection_name": self.collection_name,
                "total_documents": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value,
                "status": collection_info.status.value,
                "optimizer_status": collection_info.optimizer_status.value if collection_info.optimizer_status else "N/A"
            }
            
            logger.info(f"📊 Retrieved Qdrant stats: {stats['total_documents']} documents")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            collections = self.client.get_collections()
            return True
        except Exception:
            return False
    
    async def close(self):
        """Clean up resources"""
        try:
            # Cleanup if needed
            logger.info("🔄 Qdrant manager cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during Qdrant cleanup: {str(e)}")