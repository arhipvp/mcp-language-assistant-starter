from __future__ import annotations

import os
import re
from typing import Dict, Optional

# Основные инструменты (ранее тобой объединённые модули)
from .text import generate_sentence, translate_text
from .image import generate_image_file
from .anki import add_anki_note

# Для грубого детекта кириллицы
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def _detect_lang(text: str) -> str:
    """Вернёт 'ru' если найдена кириллица, иначе 'de'."""
    return "ru" if _CYRILLIC_RE.search(text) else "de"


def make_card(
    word: str,
    lang: Optional[str],
    deck: str,
    tag: str = "tg-auto",
) -> Dict[str, str | int]:
    """Полный цикл создания карточки Anki из одного слова.

    Front = слово на DE
    Back  = Перевод (RU) + Satz (DE) + (опционально) <img>

    Если картинка не сгенерировалась — карточка всё равно создаётся.
    """
    # 1) Определяем язык входа
    in_lang = (lang or "").strip().lower() or _detect_lang(word)

    # 2) Получаем целевое слово на немецком
    if in_lang == "de":
        word_de = word
    else:
        # слово было RU → переводим в DE
        word_de = translate_text(word, "ru", "de")

    # 3) Генерируем B1-предложение с этим словом
    sentence_de = generate_sentence(word_de)

    # 4) Переводим предложение на RU (для Back)
    translation_ru = translate_text(sentence_de, "de", "ru")

    # 5) Пытаемся сгенерировать картинку (может вернуть пустую строку)
    img_path = generate_image_file(sentence_de) or ""

    # 6) Формируем Back (без <img>; его пришьёт add_anki_note, если media_path передан)
    back_html = (
        f"<div>Перевод: {translation_ru}</div>"
        f"<div>Satz: {sentence_de}</div>"
    )

    # 7) Добавляем карточку в Anki
    note_id = add_anki_note(
        front=word_de,
        back_html=back_html,
        deck=deck,
        tags=[tag] if tag else [],
        media_path=img_path or None,  # картинка опциональна
    )

    # 8) Возвращаем краткий результат
    img_name = os.path.basename(img_path) if img_path else ""
    return {
        "note_id": note_id,
        "front": word_de,
        "back": back_html,
        "image": img_name,
    }
