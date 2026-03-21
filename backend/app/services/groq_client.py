from groq import Groq
import os
import json
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FAST_MODEL = "llama-3.1-8b-instant"      # For batch categorisation
QUALITY_MODEL = "llama-3.3-70b-versatile" # For anomaly narrative + synthesis

def call_fast(prompt: str, max_tokens: int = 1000) -> str:
    """Single call to fast model. Returns text content."""
    try:
        logger.info(f"Calling fast model {FAST_MODEL} (approx {len(prompt)//4} tokens)")
        completion = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Error calling fast model: {e}")
        return ""

def call_quality(prompt: str, system: Optional[str] = None, max_tokens: int = 2000) -> str:
    """Single call to quality model with optional system prompt."""
    try:
        logger.info(f"Calling quality model {QUALITY_MODEL} (approx {len(prompt)//4} tokens)")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        completion = client.chat.completions.create(
            model=QUALITY_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.4,
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Error calling quality model: {e}")
        return ""
