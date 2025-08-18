
from typing import List, Dict
from pydantic import BaseModel
from ..tools.yt_transcript import fetch_transcript
from ..tools.cefr_level import extract_vocab
from ..tools.grammar import check_text
from ..tools.anki_tool import add_basic_note

class LessonConfig(BaseModel):
    url: str
    deck: str
    tag: str = "auto-mcp"
    limit: int = 15
    language: str = "de"

def build_lesson(cfg: LessonConfig) -> Dict:
    text = fetch_transcript(cfg.url)
    vocab = extract_vocab(text, limit=cfg.limit)
    issues = check_text(text, language=cfg.language)

    for item in vocab:
        front = f"{item['term']}"
        back = f"{item['gloss']}\n\nExample: {item['example']}"
        add_basic_note(front, back, cfg.deck, tags=[cfg.tag])

    return {"vocab": vocab, "issues": issues, "chars": len(text)}
