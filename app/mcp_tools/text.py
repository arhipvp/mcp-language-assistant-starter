import os
import time
from typing import List
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_TEXT_MODEL = os.getenv("OPENROUTER_TEXT_MODEL", "")
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


def _chat(messages: List[dict]) -> str:
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {"model": OPENROUTER_TEXT_MODEL, "messages": messages}
    for attempt in range(3):
        try:
            resp = requests.post(CHAT_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Failed to get completion")


def generate_sentence(word_de: str) -> str:
    """Сгенерировать короткое предложение уровня B1 с заданным немецким словом."""
    messages = [
        {"role": "system", "content": "Du bist ein hilfsbereiter Sprachassistent."},
        {
            "role": "user",
            "content": f"Schreibe einen kurzen deutschen Satz auf B1-Niveau mit dem Wort '{word_de}'. Antworte nur mit dem Satz.",
        },
    ]
    return _chat(messages)


def translate_text(text: str, src: str, tgt: str) -> str:
    """Перевести текст между немецким и русским языками."""
    messages = [
        {
            "role": "system",
            "content": "You are a translation assistant for German and Russian.",
        },
        {
            "role": "user",
            "content": f"Translate from {src} to {tgt}: {text}",
        },
    ]
    return _chat(messages)
