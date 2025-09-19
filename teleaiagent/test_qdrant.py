#!/usr/bin/env python3
"""
Test Script for Qdrant Integration
Tests the Qdrant integration of the ContextManager
"""

import sys
import os
sys.path.append('src')

from utils.context_manager import ContextManager
import time

def test_qdrant_integration():
    """Tests the Qdrant integration"""
    print("🧪 Testing Qdrant integration...")
    
    # Create Context Manager
    cm = ContextManager()
    
    # Check availability
    print(f"Qdrant available: {'✅' if cm.is_qdrant_available() else '❌'}")
    
    if not cm.is_qdrant_available():
        print("Qdrant not available - start Docker container first!")
        return False
    
    # Create test message
    test_message = {
        'message_id': 12345,
        'from': {'id': 123456789, 'first_name': 'TestUser'},
        'chat': {'id': -1001234567890, 'title': 'TestChat', 'type': 'supergroup'},
        'text': 'This is a test message for Qdrant'
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
    print(f"Qdrant Documents: {stats['qdrant_documents']}")
    print(f"Qdrant Chats: {stats['qdrant_chats']}")
    
    # Test search
    print("🔍 Testing search...")
    results = cm.search_context_qdrant("test message", limit=5)
    print(f"Search results found: {len(results)}")
    
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['text'][:50]}... (score: {result['score']:.3f})")
    
    # Test semantic search
    print("🔍 Testing semantic context search...")
    context = cm.load_relevant_context_qdrant(test_message, "test message")
    if context:
        print(f"Relevant context found: {len(context.splitlines())} lines")
        print(f"Context preview: {context[:100]}...")
    else:
        print("No relevant context found")
    
    # Test chat history
    print("📝 Testing chat history...")
    history = cm.get_chat_history_qdrant(-1001234567890, days=1)
    print(f"Chat history: {len(history)} messages")
    
    print("✅ Qdrant test completed!")
    return True

if __name__ == "__main__":
    success = test_qdrant_integration()
    sys.exit(0 if success else 1)