#!/usr/bin/env python3
"""
Test script for AsyncIO TeleAI Agent
Tests the basic functionality of the async implementation
"""

import asyncio
import logging
from src.utils.ai_client import AIClient

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
    
    # Test basic AI client
    await test_ai_client()
    
    # Test concurrent requests
    await test_concurrent_requests()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())