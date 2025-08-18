import os
import re
from typing import Dict

try:
    from .translate import translate_text  # type: ignore
except Exception:  # pragma: no cover
    translate_text = None  # type: ignore

try:
    from .sentence import generate_sentence  # type: ignore
except Exception:  # pragma: no cover
    generate_sentence = None  # type: ignore

try:
    from .image import generate_image_file  # type: ignore
except Exception:  # pragma: no cover
    generate_image_file = None  # type: ignore

try:
    from .anki import add_anki_note  # type: ignore
except Exception:  # pragma: no cover
    add_anki_note = None  # type: ignore

_CYRILLIC_RE = re.compile("[\u0400-\u04FF]")

def _detect_lang(text: str) -> str:
    return "ru" if _CYRILLIC_RE.search(text) else "de"

def make_card(word: str, lang: str, deck: str, tag: str = "tg-auto") -> Dict[str, object]:
    """Create an Anki card from a given word.

    Parameters
    ----------
    word: str
        The source word.
    lang: str
        Language of the word ("ru" or "de"). If empty, it will be detected.
    deck: str
        Anki deck name.
    tag: str, default "tg-auto"
        Tag to attach to the note.
    """
    in_lang = lang or _detect_lang(word)
    if in_lang == "ru":
        if translate_text is None:
            raise RuntimeError("translate_text function is not available")
        word_de = translate_text(word, "ru", "de")
    else:
        word_de = word

    if generate_sentence is None:
        raise RuntimeError("generate_sentence function is not available")
    sentence_de = generate_sentence(word_de)

    if translate_text is None:
        raise RuntimeError("translate_text function is not available")
    translation_ru = translate_text(sentence_de, "de", "ru")

    if generate_image_file is None:
        raise RuntimeError("generate_image_file function is not available")
    img_path = generate_image_file(sentence_de)

    back_html = (
        f"<div>Перевод: {translation_ru}</div>"
        f"<div>Satz: {sentence_de}</div>"
    )

    img_name = ""
    if img_path:
        img_name = os.path.basename(img_path)
        back_html += f'<img src="{img_name}" />'

    if add_anki_note is None:
        raise RuntimeError("add_anki_note function is not available")
    note_id = add_anki_note(word_de, back_html, deck, [tag], media_path=img_path or None)

    return {"note_id": note_id, "front": word_de, "back": back_html, "image": img_name}
