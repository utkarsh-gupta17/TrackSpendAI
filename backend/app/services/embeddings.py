import os
import torch
from typing import List, Dict, Any

# Set cache directories
os.environ['TRANSFORMERS_CACHE'] = '/tmp/models'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/tmp/models'

_bi_encoder = None
_cross_encoder = None

def load_models():
    """Download and cache both models."""
    global _bi_encoder, _cross_encoder
    # Lazy import to speed up initial startup if not needed
    from sentence_transformers import SentenceTransformer, CrossEncoder
    
    print("Initializing SentenceTransformer (all-MiniLM-L6-v2)...")
    _bi_encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Initializing CrossEncoder (cross-encoder/ms-marco-MiniLM-L-6-v2)...")
    _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def get_bi_encoder():
    if _bi_encoder is None:
        load_models()
    return _bi_encoder

def get_cross_encoder():
    if _cross_encoder is None:
        load_models()
    return _cross_encoder

def embed_text(texts: List[str]) -> torch.Tensor:
    """Embed a list of strings using the bi-encoder."""
    encoder = get_bi_encoder()
    return encoder.encode(texts, convert_to_tensor=True)

def score_pairs(pairs: List[tuple]) -> List[float]:
    """Score pairs of (query, chunk) using the cross-encoder."""
    encoder = get_cross_encoder()
    return encoder.predict(pairs)
