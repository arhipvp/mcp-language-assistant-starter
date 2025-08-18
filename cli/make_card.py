#!/usr/bin/env python3
"""CLI для ручного создания карточки Anki."""

from __future__ import annotations

import argparse
import json
import sys

from app.mcp_tools import lesson


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create Anki card via lesson.make_card")
    parser.add_argument("--word", required=True, help="Слово для карточки")
    parser.add_argument(
        "--lang",
        choices=["de", "ru", "auto"],
        default="auto",
        help="Язык исходного слова (de, ru или auto)",
    )
    parser.add_argument("--deck", required=True, help="Имя колоды")
    parser.add_argument("--tag", required=True, help="Тег для карточки")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    lang = None if args.lang == "auto" else args.lang
    try:
        result = lesson.make_card(args.word, lang, args.deck, args.tag)
    except Exception as exc:  # pragma: no cover - error path
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
