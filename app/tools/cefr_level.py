
"""Naive vocab extraction and CEFR-ish tagging.
This is a stub: replace with a real model (e.g., word frequency lists + embeddings).
"""
from typing import List, Dict
import re

def extract_vocab(text: str, limit: int = 20) -> List[Dict]:
    # extremely naive: pick unique words longer than 4 chars, lowercased
    words = re.findall(r"[\wÄÖÜäöüß-]+", text, re.UNICODE)
    seen = set()
    items = []
    for w in words:
        lw = w.lower()
        if len(lw) < 5: 
            continue
        if lw in seen:
            continue
        seen.add(lw)
        items.append({
            "term": lw,
            "gloss": "(translate manually / TODO: plug translator)",
            "example": f"... {lw} ...",
            "level": "A2-B1? (heuristic)",
        })
        if len(items) >= limit:
            break
    return items
