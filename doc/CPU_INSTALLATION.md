# CPU-Only Installation Guide

## For Local Development (CPU-only)

If you want to test locally without GPU support:

```bash
# Install CPU-only PyTorch first (compatible versions)
pip install torch==2.4.0+cpu torchvision==0.19.0+cpu torchaudio==2.4.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install SentenceTransformers
pip install sentence-transformers==3.0.1

# Install remaining dependencies
pip install -r requirements.txt
```

## For Docker (Automatic CPU-only)

The Dockerfile is already configured for CPU-only installation:

```bash
docker compose build
docker compose up -d
```

## Benefits of CPU-only Setup

1. **Smaller Image Size**: ~2-3GB instead of 8-10GB with CUDA
2. **Faster Build**: No need to download large CUDA libraries
3. **Universal Compatibility**: Works on any machine
4. **Good Performance**: SentenceTransformers is efficient on CPU for text embeddings

## Performance Notes

- **Embedding Generation**: ~50-100ms per message on modern CPU
- **Model Loading**: ~2-3 seconds on first use
- **Memory Usage**: ~200-300MB for the embedding model
- **Inference**: Fast enough for real-time chat applications

The `all-MiniLM-L6-v2` model is specifically chosen for good CPU performance while maintaining high semantic quality.