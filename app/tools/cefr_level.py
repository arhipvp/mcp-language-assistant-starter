"""Vocabulary extraction with naive CEFR tagging.

This module uses a small open frequency list mapping German words to
Common European Framework of Reference (CEFR) levels.  The dataset is
stored in ``cefr_de.csv`` next to this file.  The extractor performs a
very light normalisation (lower‑casing and stripping of common suffixes)
so that inflected forms can still match the base entries in the list.

If the dataset does not contain a word, the level is reported as ``"?"``
and the gloss left empty.  This keeps the function useful even when the
vocabulary is outside the sample list.
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Dict, List

# Optional translation via DeepL if an API key is supplied.  This keeps the
# function offline by default but allows richer cards when credentials are
# present in ``.env``.
import requests
from dotenv import load_dotenv

load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

_CEFR_CACHE: Dict[str, Dict[str, str]] | None = None


def _load_cefr_vocab() -> Dict[str, Dict[str, str]]:
    """Load CEFR vocabulary from the bundled CSV file."""
    global _CEFR_CACHE
    if _CEFR_CACHE is None:
        path = Path(__file__).with_name("cefr_de.csv")
        data: Dict[str, Dict[str, str]] = {}
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data[row["term"]] = {"level": row["level"], "gloss": row["gloss"]}
        _CEFR_CACHE = data
    return _CEFR_CACHE


_SUFFIXES = ("en", "er", "e", "n", "s")


def _lemma(word: str) -> str:
    """Very small heuristic to obtain a lemma-like form."""
    for suf in _SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


def _lookup(word: str) -> Dict[str, str]:
    vocab = _load_cefr_vocab()
    entry = vocab.get(word)
    if entry:
        return entry
    return vocab.get(_lemma(word), {"level": "?", "gloss": ""})


def _translate(term: str) -> str:
    """Translate term to English using DeepL if available."""
    if not DEEPL_API_KEY:
        return ""
    try:
        resp = requests.post(
            "https://api-free.deepl.com/v2/translate",
            data={"auth_key": DEEPL_API_KEY, "text": term, "target_lang": "EN"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["translations"][0]["text"]
    except Exception:
        return ""


def extract_vocab(text: str, limit: int = 20) -> List[Dict[str, str]]:
    """Extract unique vocabulary terms from ``text``.

    Parameters
    ----------
    text:
        Input text to analyse.
    limit:
        Maximum number of vocabulary items to return.
    """
    words = re.findall(r"[\wÄÖÜäöüß-]+", text, re.UNICODE)
    seen: set[str] = set()
    items: List[Dict[str, str]] = []

    for w in words:
        lw = w.lower()
        if len(lw) < 3 or lw in seen:
            continue
        seen.add(lw)
        entry = _lookup(lw)
        gloss = entry["gloss"] or _translate(lw)
        items.append(
            {
                "term": lw,
                "gloss": gloss,
                "example": f"... {w} ...",
                "level": entry["level"],
            }
        )
        if len(items) >= limit:
            break
    return items
