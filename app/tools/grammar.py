
from typing import List, Dict
import requests

LT_URL = "http://localhost:8010"

def check_text(text: str, language: str = "de") -> List[Dict]:
    try:
        resp = requests.post(f"{LT_URL}/v2/check", data={
            "text": text, "language": language
        }, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("matches", [])
    except Exception as e:
        return [{"error": str(e)}]
