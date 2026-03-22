import os
import json
from pathlib import Path
from app.services.groq_client import call_fast

# Get absolute path to the backend directory
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "data" / "knowledge_base"
_knowledge_base_text: str = ""  # Loaded once at startup, plain string

def load_knowledge_base() -> None:
    """
    Called once at server startup via lifespan.
    Reads all .txt files from knowledge_base/ directory.
    Concatenates them into a single string with clear source labels.
    Stores in module-level variable _knowledge_base_text.
    NO embeddings, NO models, NO vector operations.
    Just reading text files into memory — ~50KB total.
    """
    global _knowledge_base_text
    chunks = []
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"Knowledge base directory {KNOWLEDGE_BASE_DIR} not found.")
        return

    for txt_file in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):
        content = txt_file.read_text(encoding="utf-8").strip()
        source_name = txt_file.stem.replace("_", " ").title()
        chunks.append(f"=== SOURCE: {source_name} ===\n{content}")
    
    _knowledge_base_text = "\n\n".join(chunks)
    print(f"Knowledge base loaded: {len(_knowledge_base_text)} characters from "
          f"{len(list(KNOWLEDGE_BASE_DIR.glob('*.txt')))} files")


def build_rag_query(summary: dict, anomalies: list) -> str:
    """
    Build a specific, targeted query from the user's actual spending data.
    Never use a generic fixed query — always construct from real data.

    Logic:
    - Find top spending category (by total amount)
    - Check savings rate (credit - debit) / credit
    - Check if any Investment category transactions exist
    - Check if anomalies were detected
    """
    if not summary:
        return "general financial health personal savings India"

    top_category = max(
        summary.get("by_category", {}).items(),
        key=lambda x: x[1].get("total", 0),
        default=("Other", {})
    )[0]

    savings_rate = summary.get("savings_rate", 0)
    has_investment = "Investment" in summary.get("by_category", {})
    has_anomalies = len(anomalies) > 0

    parts = []
    parts.append(
        f"{top_category} is top spending category at "
        f"{summary.get('by_category', {}).get(top_category, {}).get('percentage', 0):.0f}% "
        f"of total expenses. Recommended {top_category.lower()} budget India."
    )

    if savings_rate < 20:
        parts.append(
            f"Savings rate is {savings_rate:.0f}%. "
            f"Minimum recommended savings rate India emergency fund."
        )
    if not has_investment:
        parts.append(
            "No SIP or mutual fund investments found. "
            "Starting investments Section 80C PPF ELSS India."
        )
    if has_anomalies:
        parts.append("Suspicious transactions detected. Financial safety India.")

    return " ".join(parts)


def retrieve_relevant_guidance(query: str) -> dict:
    """
    LLM-as-Retriever: sends the full knowledge base + query to Groq in one call.
    Groq identifies the 3 most relevant passages and returns them structured.
    """
    if not _knowledge_base_text:
        return _get_fallback_guidance()

    prompt = f"""You are a financial knowledge retrieval system.

KNOWLEDGE BASE:
{_knowledge_base_text}

USER QUERY:
{query}

Task: Identify the 3 most relevant passages from the knowledge base that directly
address this query. For each passage, extract the key actionable insight.

Respond ONLY with valid JSON in this exact format:
{{
  "passages": [
    {{
      "source": "source name from the === SOURCE === header",
      "text": "the most relevant 2-3 sentences from that source",
      "relevance_reason": "one sentence explaining why this is relevant to the query"
    }}
  ],
  "combined_context": "a single paragraph combining the key guidance from all 3 passages, written as coherent advice"
}}

Important: Extract actual text from the knowledge base. Do not make up content."""

    try:
        response = call_fast(prompt, max_tokens=800)
        # Strip markdown code blocks if present
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        result = json.loads(clean.strip())
        return result
    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return _get_fallback_guidance()


def _get_fallback_guidance() -> dict:
    """Minimal fallback if knowledge base or LLM call fails."""
    return {
        "passages": [
            {
                "source": "General Guidance",
                "text": "Aim to save at least 20% of your monthly income. "
                        "Build an emergency fund covering 3-6 months of expenses.",
                "relevance_reason": "Universal financial health principles"
            }
        ],
        "combined_context": "Follow the 50/30/20 rule: 50% on needs, 30% on wants, "
                           "20% on savings. Start a SIP in mutual funds early. "
                           "Use Section 80C to save up to ₹1.5 lakh in taxes annually."
    }
