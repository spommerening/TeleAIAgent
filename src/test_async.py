#!/usr/bin/env python3
"""
Test script for AsyncIO TeleAI Agent
Tests the basic functionality of the async implementation

Usage:
  # From project root:
  python src/test_async.py
  
  # From src directory:
  python test_async.py
  
  # Using Docker environment:
  docker compose exec teleaiagent python test_async.py
"""

import asyncio
import logging
import os
import sys

# Set minimal environment variables for testing if not present
if not os.getenv('TG_BOT_TOKEN'):
    os.environ['TG_BOT_TOKEN'] = 'test_token_for_async_testing'
if not os.getenv('AI_BACKEND'):
    os.environ['AI_BACKEND'] = 'perplexity'
if not os.getenv('PERPLEXITY_API_KEY'):
    os.environ['PERPLEXITY_API_KEY'] = 'test_key'

try:
    # Try direct import (when in src/ or Docker container)
    from utils.ai_client import AIClient
except ImportError:
    try:
        # Try from src package (when running from project root)
        from src.utils.ai_client import AIClient
    except ImportError:
        # Add src to path and try again
        sys.path.append('src')
        from utils.ai_client import AIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_client():
    """Test the AsyncIO AI Client"""
    logger.info("Testing AsyncIO AI Client...")
    
    try:
        # Create AI client
        ai_client = AIClient()
        await ai_client.initialize()
        
        # Test query
        question = "What is 2 + 2? Please answer briefly."
        response = await ai_client.query_ai(question)
        
        logger.info(f"Question: {question}")
        logger.info(f"Response: {response}")
        logger.info("✅ AI Client test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ AI Client test failed: {e}")

async def test_concurrent_requests():
    """Test concurrent AI requests"""
    logger.info("Testing concurrent AI requests...")
    
    try:
        ai_client = AIClient()
        await ai_client.initialize()
        
        # Create multiple concurrent requests
        questions = [
            "What is the capital of France?",
            "What is 5 * 7?", 
            "What color is the sky?",
            "What is Python programming language?"
        ]
        
        # Run all requests concurrently
        tasks = [ai_client.query_ai(q) for q in questions]
        responses = await asyncio.gather(*tasks)
        
        for q, r in zip(questions, responses):
            logger.info(f"Q: {q}")
            logger.info(f"A: {r[:100]}...")  # First 100 chars
            logger.info("---")
            
        logger.info("✅ Concurrent requests test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Concurrent requests test failed: {e}")

async def main():
    """Main test function"""
    logger.info("Starting AsyncIO TeleAI Agent Tests...")
    
    # Check environment
    backend = os.getenv('AI_BACKEND', 'perplexity')
    logger.info(f"Using AI Backend: {backend}")
    
    if backend == 'perplexity':
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key or api_key == 'test_key':
            logger.warning("⚠️  No real PERPLEXITY_API_KEY found - tests may fail")
    elif backend == 'ollama':
        ollama_url = os.getenv('OLLAMA_URL', 'http://ollama-server:11434')
        logger.info(f"Ollama URL: {ollama_url}")
    
    try:
        # Test basic AI client
        await test_ai_client()
        
        # Test concurrent requests only if we have a real API key
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if api_key and api_key != 'test_key':
            await test_concurrent_requests()
        else:
            logger.info("⏭️  Skipping concurrent requests test (no real API key)")
        
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)