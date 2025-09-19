#!/usr/bin/env python3
"""
Test CPU Configuration
Verify that PyTorch and SentenceTransformers are using CPU-only mode
"""

import sys
import os

# Set dummy environment variables
os.environ['TG_BOT_TOKEN'] = 'dummy'
os.environ['PERPLEXITY_API_KEY'] = 'dummy'

print("🔧 Testing CPU-only configuration...")

# Test PyTorch
try:
    import torch
    print(f"✅ PyTorch version: {torch.__version__}")
    print(f"💻 CUDA available: {torch.cuda.is_available()}")
    print(f"🖥️  CPU cores: {torch.get_num_threads()}")
    
    if torch.cuda.is_available():
        print("⚠️  GPU detected but will use CPU-only mode")
    else:
        print("✅ CPU-only mode confirmed")
        
except ImportError as e:
    print(f"❌ PyTorch not available: {e}")

# Test SentenceTransformers
try:
    from sentence_transformers import SentenceTransformer
    print("✅ SentenceTransformers available")
    
    # Test model loading on CPU
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    print("✅ Model loaded successfully on CPU")
    
    # Test embedding generation
    test_text = "This is a test sentence."
    embedding = model.encode(test_text)
    print(f"✅ Embedding generated: {embedding.shape} dimensions")
    
except ImportError as e:
    print(f"❌ SentenceTransformers not available: {e}")
except Exception as e:
    print(f"❌ Error testing SentenceTransformers: {e}")

# Test ContextManager CPU configuration
try:
    sys.path.append('.')
    from utils.context_manager import ContextManager
    
    print("🧪 Testing ContextManager with CPU embeddings...")
    cm = ContextManager()
    
    if cm.embedding_model:
        print("✅ ContextManager embedding model loaded successfully")
        
        # Test embedding
        test_embedding = cm._get_embedding("Test message")
        print(f"✅ Embedding generated: {len(test_embedding)} dimensions")
    else:
        print("❌ ContextManager embedding model not loaded")
        
except Exception as e:
    print(f"❌ Error testing ContextManager: {e}")

print("🎉 CPU configuration test completed!")