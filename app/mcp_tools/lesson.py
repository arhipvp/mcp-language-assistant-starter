from __future__ import annotations

import os
import re
from typing import Dict, Optional
import importlib

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
    # TODO: ref_image: str | bytes | None = None
) -> Dict[str, str | int]:
    """Полный цикл создания карточки Anki из одного слова.

    Front = слово на DE
    Back  = Перевод (RU) + Satz (DE) + (опционально) <img>

    Если картинка не сгенерировалась — карточка всё равно создаётся.
    """
    # Динамические импорты, чтобы тесты могли подменять модули через sys.modules
    text_mod = importlib.import_module("app.mcp_tools.text")
    image_mod = importlib.import_module("app.mcp_tools.image")
    anki_mod = importlib.import_module("app.mcp_tools.anki")

    gen_sentence = getattr(text_mod, "generate_sentence")
    translate = getattr(text_mod, "translate_text")
    add_note = getattr(anki_mod, "add_anki_note")

    # 1) Определяем язык входа
    in_lang = (lang or "").strip().lower() or _detect_lang(word)

    # 2) Получаем целевое слово на немецком
    if in_lang == "de":
        word_de = word
    else:
        # слово было RU → переводим в DE
        word_de = translate(word, "ru", "de")

    # 3) Генерируем B1-предложение с этим словом
    sentence_de = gen_sentence(word_de)

    # 4) Переводим предложение на RU (для Back)
    translation_ru = translate(sentence_de, "de", "ru")

    # 5) Пытаемся сгенерировать картинку (может вернуть пустую строку)
    provider = os.getenv("IMAGE_PROVIDER", "openrouter").strip().lower()
    if provider == "genapi" and hasattr(image_mod, "generate_image_file_genapi"):
        # TODO: при добавлении аргумента ref_image в make_card
        #       прокинуть его в generate_image_file_genapi(sentence_de, ref_image=ref_image)
        img_path = image_mod.generate_image_file_genapi(sentence_de) or ""
    elif provider == "none":
        img_path = ""
    else:  # по умолчанию — openrouter (или неизвестный провайдер)
        gen_image = getattr(image_mod, "generate_image_file")
        img_path = gen_image(sentence_de) or ""

    # 6) Формируем Back (без <img>; его пришьёт add_anki_note, если media_path передан)
    back_html = (
        f"<div>Перевод: {translation_ru}</div>"
        f"<div>Satz: {sentence_de}</div>"
    )

    # 7) Добавляем карточку в Anki
    note_id = add_note(
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
