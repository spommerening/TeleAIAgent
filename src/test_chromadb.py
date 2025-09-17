#!/usr/bin/env python3
"""
Test Script for ChromaDB Integration
Tests the ChromaDB integration of the ContextManager
"""

import sys
import os
sys.path.append('src')

from utils.context_manager import ContextManager
import time

def test_chromadb_integration():
    """Tests the ChromaDB integration"""
    print("🧪 Testing ChromaDB integration...")
    
    # Create Context Manager
    cm = ContextManager()
    
    # Check availability
    print(f"ChromaDB available: {'✅' if cm.is_chromadb_available() else '❌'}")
    
    if not cm.is_chromadb_available():
        print("ChromaDB not available - start Docker container first!")
        return False
    
    # Create test message
    test_message = {
        'message_id': 12345,
        'from': {'id': 123456789, 'first_name': 'TestUser'},
        'chat': {'id': -1001234567890, 'title': 'TestChat', 'type': 'supergroup'},
        'text': 'This is a test message for ChromaDB'
    }
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    print("📝 Storing test message...")
    try:
        cm.store_context(test_message, timestamp)
        print("✅ Message successfully stored!")
    except Exception as e:
        print(f"❌ Error storing: {e}")
        return False
    
    # Retrieve statistics
    print("📊 Retrieving statistics...")
    stats = cm.get_context_stats()
    print(f"ChromaDB Documents: {stats['chromadb_documents']}")
    print(f"ChromaDB Chats: {stats['chromadb_chats']}")
    
    # Test search
    print("🔍 Testing search...")
    results = cm.search_context_chromadb("test message", limit=5)
    print(f"Search results found: {len(results)}")
    
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['text'][:50]}...")
    
    print("✅ ChromaDB test completed!")
    return True

if __name__ == "__main__":
    success = test_chromadb_integration()
    sys.exit(0 if success else 1)
