#!/usr/bin/env python3
"""
Test Script for Description-Based Workflow
Tests the new simplified description generation workflow
"""

import asyncio
import json
import os
import sys
import requests
from pathlib import Path
from PIL import Image
import io

# Add teleaiagent path for imports
sys.path.append('teleaiagent')

from utils.tagger_client import TaggerClient

def create_test_image():
    """Create a simple colorful test image"""
    # Create a 100x100 pixel image with some colors
    image = Image.new('RGB', (100, 100))
    pixels = []
    
    # Create a simple pattern
    for y in range(100):
        for x in range(100):
            if x < 50 and y < 50:
                pixels.append((255, 0, 0))  # Red
            elif x >= 50 and y < 50:
                pixels.append((0, 255, 0))  # Green  
            elif x < 50 and y >= 50:
                pixels.append((0, 0, 255))  # Blue
            else:
                pixels.append((255, 255, 0))  # Yellow
    
    image.putdata(pixels)
    
    # Convert to bytes
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

async def test_description_workflow():
    """Test the new description-based workflow"""
    print("🧪 Testing Description-Based Workflow...")
    print("=" * 50)
    
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
        
        # Test 2: Process a test image with description workflow
        print("🖼️ Testing description generation...")
        
        # Create a colorful test image
        test_image_data = create_test_image()
        print(f"Created test image: {len(test_image_data)} bytes")
        
        # Prepare test metadata
        test_metadata = {
            'chat_id': -1001234567890,
            'chat_title': 'Description Test Chat',
            'chat_type': 'supergroup',
            'user_id': 123456789,
            'user_name': 'Test User',
            'message_id': 12345,
            'timestamp': '2025-09-20 12:00:00',
            'date': '2025-09-20',
            'file_id': 'test_description_image_001',
            'file_size': len(test_image_data),
            'has_caption': False,
            'caption': ''
        }
        
        # Send to tagger service for processing
        print("🤖 Sending image for description generation...")
        result = await tagger_client.process_image(
            image_data=test_image_data,
            telegram_metadata=test_metadata,  # Pass as dict, not JSON string
            filename="test_description_image.png"
        )
        
        if result and result.get('status') == 'success':
            result_data = result.get('result', {})
            description = result_data.get('description', 'No description')
            quality_score = result_data.get('quality_score', 0)
            storage_path = result_data.get('storage_path', 'No path')
            document_id = result_data.get('document_id', 'No ID')
            
            print("✅ Description generation successful!")
            print(f"   📝 Description: {description}")
            print(f"   📊 Quality Score: {quality_score:.2f}")
            print(f"   📁 Storage Path: {storage_path}")
            print(f"   🆔 Document ID: {document_id}")
            
            # Test 3: Search for similar images using description
            print("🔍 Testing description-based search...")
            
            # Search for images with similar content
            search_query = "colorful image with red green blue yellow"
            try:
                search_url = f"http://localhost:7777/search-similar?query={search_query}&limit=5"
                response = requests.get(search_url)
                
                if response.status_code == 200:
                    search_results = response.json()
                    print(f"✅ Found {len(search_results)} similar images")
                    for i, result in enumerate(search_results[:3]):  # Show first 3
                        print(f"   {i+1}. Score: {result.get('score', 0):.3f}, Description: {result.get('description', 'N/A')[:60]}...")
                else:
                    print(f"⚠️ Search request failed with status: {response.status_code}")
                    
            except Exception as search_error:
                print(f"⚠️ Search test failed: {search_error}")
            
            return True
        else:
            print("❌ Description generation failed")
            print(f"Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def test_direct_api():
    """Test the tagger API directly"""
    print("🔗 Testing Direct API Access...")
    
    try:
        # Test health endpoint
        health_response = requests.get("http://localhost:7777/health")
        print(f"Health endpoint: {health_response.status_code} - {health_response.json()}")
        
        # Test stats endpoint  
        stats_response = requests.get("http://localhost:7777/stats")
        print(f"Stats endpoint: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"   Qdrant documents: {stats.get('qdrant', {}).get('total_documents', 0)}")
            print(f"   Storage images: {stats.get('storage', {}).get('total_images', 0)}")
        
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")

def check_docker_services():
    """Check if required Docker services are running"""
    print("🐳 Checking Docker services...")
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'compose', 'ps', '--services', '--filter', 'status=running'], 
                              capture_output=True, text=True, cwd='/home/appl/TeleAIAgent')
        
        running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        required_services = ['tagger', 'qdrant', 'ollama']
        for service in required_services:
            if service in running_services:
                print(f"✅ {service.capitalize()} Service: Running")
            else:
                print(f"❌ {service.capitalize()} Service: Not running")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Description-Based Workflow Tests...")
    print("=" * 50)
    
    # Check Docker services
    if not check_docker_services():
        print("\n❌ Required Docker services are not running!")
        print("Run: docker compose up -d")
        return
    
    # Run tests
    await test_direct_api()
    print()
    
    success = await test_description_workflow()
    
    print("=" * 50)
    if success:
        print("🎉 All description workflow tests PASSED!")
    else:
        print("❌ Some tests FAILED!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())