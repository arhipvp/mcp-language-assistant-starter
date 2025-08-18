from __future__ import annotations

from typing import Dict

from .text import generate_sentence, translate_text
from .image import generate_image_file
from .anki import add_anki_note



def make_card(word: str, lang: str, deck: str, tag: str) -> Dict[str, str | int]:
    """Полный цикл создания карточки из одного слова."""
    lang = lang.lower()
    if lang == "de":
        word_de = word
        word_ru = translate_text(word, "de", "ru")
    else:
        word_ru = word
        word_de = translate_text(word, "ru", "de")
    sentence_de = generate_sentence(word_de)
    sentence_ru = translate_text(sentence_de, "de", "ru")
    image_path = generate_image_file(sentence_de)
    back_text = f"{word_ru}<br>{sentence_de}<br>{sentence_ru}"
    note_id = add_anki_note(word_de, back_text, deck, [tag] if tag else [], image_path)
    return {
        "note_id": note_id,
        "front": word_de,
        "back": back_text,
        "image": image_path,
    }
