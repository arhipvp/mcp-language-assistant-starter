from __future__ import annotations

import os
import re
from typing import Dict, Optional

# Основные инструменты (ранее тобой объединённые модули)
from .text import generate_sentence, translate_text
from . import image
from .anki import add_anki_note

# Оригинальные ссылки для определения перезаписанных зависимостей
_ORIG_GENERATE_SENTENCE = generate_sentence
_ORIG_TRANSLATE_TEXT = translate_text
_ORIG_ADD_ANKI_NOTE = add_anki_note
_ORIG_GENERATE_IMAGE_FILE = image.generate_image_file

# Совместимость со старыми тестами/патчами
generate_image_file = image.generate_image_file


def _refresh_deps() -> None:
    """Reload dependency modules if they weren't monkeypatched."""
    from importlib import import_module
    global generate_sentence, translate_text, add_anki_note, generate_image_file, image

    if generate_sentence is _ORIG_GENERATE_SENTENCE or translate_text is _ORIG_TRANSLATE_TEXT:
        text_mod = import_module("app.mcp_tools.text")
        if generate_sentence is _ORIG_GENERATE_SENTENCE:
            generate_sentence = text_mod.generate_sentence
        if translate_text is _ORIG_TRANSLATE_TEXT:
            translate_text = text_mod.translate_text

    if add_anki_note is _ORIG_ADD_ANKI_NOTE:
        anki_mod = import_module("app.mcp_tools.anki")
        add_anki_note = anki_mod.add_anki_note

    if generate_image_file is _ORIG_GENERATE_IMAGE_FILE or not hasattr(image, "generate_image_file_genapi"):
        image_mod = import_module("app.mcp_tools.image")
        if generate_image_file is _ORIG_GENERATE_IMAGE_FILE:
            generate_image_file = image_mod.generate_image_file
        image = image_mod

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
    # Обновляем зависимости, если они не были замоканы
    _refresh_deps()
    image_mod = image

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
    provider = os.getenv("IMAGE_PROVIDER", "openrouter").strip().lower()
    if provider == "genapi":
        gen = getattr(image_mod, "generate_image_file_genapi", lambda *_: "")
        img_path = gen(sentence_de) or ""
    elif provider == "none":
        img_path = ""
    else:  # openrouter или неизвестный провайдер
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
