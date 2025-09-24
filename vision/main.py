"""
FastAPI Vision Microservice
Main entry point for the image vision service
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from config import Config
from handlers.image_handler import ImageHandler
from utils.ollama_client import OllamaClient
from utils.qdrant_client import QdrantManager
from utils.file_manager import FileManager

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Configure HTTP libraries logging
if not Config.DEBUG_HTTP_LIBRARIES:
    # Set HTTP libraries to higher level (less spam)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logger.info("HTTP debug logging disabled (Config.DEBUG_HTTP_LIBRARIES = False)")
else:
    logger.info("HTTP debug logging enabled (Config.DEBUG_HTTP_LIBRARIES = True)")

# Global service managers
ollama_client: Optional[OllamaClient] = None
qdrant_manager: Optional[QdrantManager] = None
file_manager: Optional[FileManager] = None
image_handler: Optional[ImageHandler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global ollama_client, qdrant_manager, file_manager, image_handler
    
    logger.info("🚀 Starting Vision microservice...")
    
    try:
        # Initialize service managers
        logger.info("🔧 Initializing service managers...")
        
        ollama_client = OllamaClient()
        qdrant_manager = QdrantManager()
        file_manager = FileManager()
        image_handler = ImageHandler(ollama_client, file_manager, qdrant_manager)
        
        # Initialize connections
        await ollama_client.initialize()
        await qdrant_manager.initialize()
        
        logger.info("✅ Vision service initialized successfully")
        
        yield  # Service is running
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize vision service: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("🔄 Shutting down vision service...")

        if ollama_client:
            await ollama_client.close()
        if qdrant_manager:
            await qdrant_manager.close()

        logger.info("✅ Vision service shut down complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Image Vision Microservice",
    description="Microservice for AI-powered image vision with Ollama and Qdrant integration",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Image Vision Microservice", "status": "running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "service": "healthy",
        "ollama": "unknown",
        "qdrant": "unknown",
        "file_system": "unknown"
    }
    
    try:
        # Check Ollama connection
        if ollama_client and await ollama_client.health_check():
            health_status["ollama"] = "healthy"
        else:
            health_status["ollama"] = "unhealthy"
            
        # Check Qdrant connection
        if qdrant_manager and await qdrant_manager.health_check():
            health_status["qdrant"] = "healthy"
        else:
            health_status["qdrant"] = "unhealthy"
            
        # Check file system
        if file_manager and file_manager.health_check():
            health_status["file_system"] = "healthy"
        else:
            health_status["file_system"] = "unhealthy"
            
        # Overall health
        if all(status == "healthy" for status in health_status.values()):
            return {"status": "healthy", "details": health_status}
        else:
            return {"status": "degraded", "details": health_status}
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        health_status["service"] = "unhealthy"
        return {"status": "unhealthy", "details": health_status, "error": str(e)}


@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    try:
        stats = {
            "service": {
                "name": Config.SERVICE_NAME,
                "version": "1.0.0",
                "status": "running"
            }
        }
        
        # Add Qdrant stats if available
        if qdrant_manager:
            qdrant_stats = await qdrant_manager.get_stats()
            stats["qdrant"] = qdrant_stats
            
        # Add file system stats if available  
        if file_manager:
            file_stats = file_manager.get_stats()
            stats["storage"] = file_stats
            
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/search-similar")
async def search_similar_images(
    query: str,
    limit: int = 10
):
    """
    Search for images with similar descriptions
    
    Args:
        query: Text query to search for
        limit: Maximum number of results to return
        
    Returns:
        List of similar images with metadata and similarity scores
    """
    try:
        logger.info(f"🔍 Searching for similar images: '{query}' (limit={limit})")
        
        results = await image_handler.search_similar_images(query, limit)
        
        logger.info(f"✅ Search completed: {len(results)} results found")
        return results
        
    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def main():
    """Main function to start the service"""
    # Configure basic logging for uvicorn
    logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
    
    logger.info(f"🚀 Starting Image Vision Microservice on {Config.SERVICE_HOST}:{Config.SERVICE_PORT}")
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(
        "main:app",
        host=Config.SERVICE_HOST,
        port=Config.SERVICE_PORT,
        reload=False,  # Disable in production
        log_level=Config.LOG_LEVEL.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()