import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from app.services.embeddings import get_bi_encoder, get_cross_encoder

# Get absolute path to the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
_corpus = [] # Global in-memory corpus [{text, source_file, embedding}]

def load_and_chunk_knowledge_base():
    global _corpus
    _corpus = []
    
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"Knowledge base directory {KNOWLEDGE_BASE_DIR} not found.")
        return

    bi_encoder = get_bi_encoder()
    
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith('.txt'):
            with open(os.path.join(KNOWLEDGE_BASE_DIR, filename), 'r') as f:
                content = f.read()
                
            # Chunking: split on '. ' then regroup to ~300 tokens
            sentences = content.split('. ')
            current_chunk = []
            current_len = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence: continue
                
                # Rough token estimate
                tokens = len(sentence.split())
                if current_len + tokens > 300 and current_chunk:
                    text = ". ".join(current_chunk) + "."
                    _corpus.append({
                        "text": text,
                        "source_file": filename,
                        "embedding": bi_encoder.encode(text)
                    })
                    # 50-token overlap (approx 2 sentences)
                    current_chunk = current_chunk[-2:] if len(current_chunk) > 2 else []
                    current_len = sum(len(s.split()) for s in current_chunk)
                
                current_chunk.append(sentence)
                current_len += tokens
            
            if current_chunk:
                text = ". ".join(current_chunk) + "."
                _corpus.append({
                    "text": text,
                    "source_file": filename,
                    "embedding": bi_encoder.encode(text)
                })
    
    print(f"Loaded {len(_corpus)} chunks into memory.")

def build_rag_query(summary: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> str:
    if not summary:
        return "general financial health personal savings India"
        
    # Logic from spec
    top_cat = "N/A"
    if summary.get('by_category'):
        top_cat = max(summary['by_category'].items(), key=lambda x: x[1]['total'])[0]
    
    debit = summary.get('total_debit', 0)
    credit = summary.get('total_credit', 0)
    savings_rate = (credit - debit) / credit * 100 if credit > 0 else -100
    
    has_info_on_investment = any(cat in summary.get('by_category', {}) for cat in ['Investment', 'Insurance'])
    
    queries = []
    if top_cat in ['Food & Dining', 'Shopping', 'Entertainment']:
        queries.append(f"recommended {top_cat.lower()} spending percentage monthly income India")
        
    if savings_rate < 20:
        queries.append("minimum savings rate recommendation India emergency fund RBI")
    
    if not has_info_on_investment:
        queries.append("importance of starting SIP mutual fund investment India young professionals")
        
    if anomalies:
        queries.append("unusual transactions financial safety")
        
    final_query = " ".join(queries[:3]) # Limit to 3 angles
    return final_query or "general financial health personal savings India"

def retrieve_and_rerank(query: str, top_n: int = 5) -> List[Dict[str, Any]]:
    global _corpus
    if not _corpus:
        return []
        
    bi_encoder = get_bi_encoder()
    query_emb = bi_encoder.encode(query)
    
    # Stage 1: Bi-encoder cosine similarity
    candidates = []
    for chunk in _corpus:
        score = np.dot(query_emb, chunk['embedding']) / (np.linalg.norm(query_emb) * np.linalg.norm(chunk['embedding']))
        candidates.append({
            "text": chunk['text'],
            "source_file": chunk['source_file'],
            "score": float(score)
        })
    
    candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)[:15]
    
    # Stage 2: Cross-encoder re-ranking
    cross_encoder = get_cross_encoder()
    pairs = [(query, c['text']) for c in candidates]
    rerank_scores = cross_encoder.predict(pairs)
    
    for i, score in enumerate(rerank_scores):
        candidates[i]['score'] = float(score)
        
    final_top = sorted(candidates, key=lambda x: x['score'], reverse=True)[:top_n]
    return final_top
