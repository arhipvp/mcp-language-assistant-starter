from __future__ import annotations

from typing import List, Dict

from .lesson import make_card


def make_cards_from_list(words: List[str], lang: str, deck: str, tag: str) -> List[Dict]:
    """Создать несколько карточек из списка слов.

    Для каждого слова вызывает :func:`make_card`. Если при обработке слова
    происходит исключение, оно не прерывает цикл, а добавляется в результат в
    виде словаря ``{"word": word, "error": str(exc)}``.
    """
    results: List[Dict] = []
    for word in words:
        try:
            results.append(make_card(word, lang, deck, tag))
        except Exception as exc:  # pragma: no cover - защитный catch
            results.append({"word": word, "error": str(exc)})
    return results
