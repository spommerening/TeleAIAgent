#!/usr/bin/env python3
"""
Test Script for Tagger Service Integration
Tests the complete flow from image upload to Qdrant storage
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add teleaiagent path for imports
sys.path.append('teleaiagent')

from utils.tagger_client import TaggerClient

async def test_tagger_service():
    """Test the tagger service integration"""
    print("🧪 Testing Tagger Service Integration...")
    
    # Initialize tagger client
    tagger_client = TaggerClient("http://localhost:7777")
    await tagger_client.initialize()
    
    try:
        # Test 1: Health check
        print("🏥 Testing health check...")
        health = await tagger_client.health_check()
        print(f"Health check: {'✅ Healthy' if health else '❌ Unhealthy'}")
        
        if not health:
            print("❌ Tagger service is not healthy. Make sure docker-compose is running.")
            return False
        
        # Test 2: Service stats
        print("📊 Getting service stats...")
        stats = await tagger_client.get_tagger_stats()
        print(f"Service stats: {json.dumps(stats, indent=2)}")
        
        # Test 3: Process a test image (create a simple test image)
        print("🖼️ Testing image processing...")
        
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = create_test_image()
        
        # Prepare test metadata
        test_metadata = {
            'chat_id': -1001234567890,
            'chat_title': 'Test Chat',
            'chat_type': 'supergroup',
            'user_id': 123456789,
            'user_name': 'TestUser',
            'message_id': 12345,
            'timestamp': '2025-09-19 10:00:00',
            'date': '2025-09-19',
            'file_id': 'test_image_123',
            'file_size': len(test_image_data),
            'has_caption': True,
            'caption': 'This is a test image for the tagger service'
        }
        
        # Process image
        result = await tagger_client.process_image(
            image_data=test_image_data,
            telegram_metadata=test_metadata,
            filename="test_image.png"
        )
        
        print(f"✅ Image processing result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Tags: {result.get('result', {}).get('tags', [])}")
        print(f"   File path: {result.get('result', {}).get('file_path')}")
        print(f"   Document ID: {result.get('result', {}).get('document_id')}")
        
        # Test 4: Search for similar images
        print("🔍 Testing similar image search...")
        tags = result.get('result', {}).get('tags', [])
        if tags:
            similar = await tagger_client.search_similar_images(
                tags=tags[:3],  # Use first 3 tags
                limit=3
            )
            print(f"✅ Similar images found: {len(similar)}")
        
        print("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        await tagger_client.close()


def create_test_image():
    """Create a minimal test image (1x1 PNG)"""
    # Minimal PNG file (1x1 pixel, transparent)
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # Color type, etc.
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,  # Compressed data
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,  # 
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
        0x42, 0x60, 0x82
    ])
    return png_data


async def test_docker_services():
    """Test if all Docker services are running"""
    print("🐳 Checking Docker services...")
    
    services_to_check = [
        ("http://localhost:7777/health", "Tagger Service"),
        ("http://localhost:6333/collections", "Qdrant Service"),
    ]
    
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        for url, name in services_to_check:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        print(f"✅ {name}: Running")
                    else:
                        print(f"⚠️  {name}: Status {response.status}")
            except Exception as e:
                print(f"❌ {name}: Not accessible ({e})")


async def main():
    """Main test function"""
    print("🚀 Starting Tagger Service Integration Tests...")
    print("=" * 50)
    
    # Check Docker services first
    await test_docker_services()
    print()
    
    # Test tagger service
    success = await test_tagger_service()
    
    print("=" * 50)
    if success:
        print("🎉 All integration tests PASSED!")
        return 0
    else:
        print("❌ Integration tests FAILED!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)