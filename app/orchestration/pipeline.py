from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel

from ..tools.yt_transcript import fetch_transcript
from ..tools.cefr_level import extract_vocab
from ..tools.grammar import check_text
from ..tools.anki_tool import add_basic_note
from ..tools.tts import speak_to_file


class LessonConfig(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    deck: str
    tag: str = "auto-mcp"
    limit: int = 15
    language: str = "de"
    tts: bool = False


def build_lesson(cfg: LessonConfig) -> Dict:
    """Build a lesson from a YouTube URL or raw text."""
    if cfg.text:
        text = cfg.text
    elif cfg.url:
        text = fetch_transcript(cfg.url)
    else:
        raise ValueError("Either 'url' or 'text' must be provided")

    vocab = extract_vocab(text, limit=cfg.limit)
    issues = check_text(text, language=cfg.language)

    for item in vocab:
        front = item["term"]
        back = f"{item['gloss']}\n\nExample: {item['example']}"
        audio_path = None
        if cfg.tts:
            audio_path = speak_to_file(item["example"], f"{item['term']}.mp3")
        add_basic_note(front, back, cfg.deck, tags=[cfg.tag], audio_path=audio_path)
        item["audio"] = audio_path

    return {"vocab": vocab, "issues": issues, "chars": len(text)}
