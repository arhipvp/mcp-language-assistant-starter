from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from app import setup_logging, log_effective_settings
from app.mcp_tools.lesson import make_card
from app.settings import settings

TOKEN = settings.TELEGRAM_BOT_TOKEN
DECK = settings.ANKI_DECK
TAG = settings.ANKI_TAG

_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_HTML_TAG_RE = re.compile(r"<[^>]+>")

MEDIA_DIR = Path("media")


def _detect_lang(word: str) -> str:
    return "ru" if _CYRILLIC_RE.search(word) else "de"


def _image_fs_path(image_name: Optional[str]) -> Optional[Path]:
    """Построить путь до локального файла картинки, если он есть."""
    if not image_name:
        return None
    p = MEDIA_DIR / image_name
    return p if p.exists() else None


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger = logging.getLogger(__name__)
    logger.info("Update received", extra={"step": "bot.update"})
    text = (update.message.text or "").strip()
    if not text:
        return
    # Ограничимся одним словом, чтобы избежать мусора
    if " " in text:
        await update.message.reply_text("Пришлите одно слово (DE или RU).")
        return

    lang = _detect_lang(text)

    run_id = uuid.uuid4().hex[:8]
    logger.info("Pipeline started", extra={"step": "pipeline", "run_id": run_id})

    try:
        loop = asyncio.get_running_loop()
        result: Dict[str, Any] = await loop.run_in_executor(
            None, lambda: make_card(text, lang, DECK, TAG)
        )

        front = str(result.get("front", text))
        back_html = str(result.get("back", ""))
        back_plain = _HTML_TAG_RE.sub(" ", back_html)
        back_plain = " ".join(back_plain.split()).strip()

        image_name = result.get("image") or result.get("image_path")  # совместимость
        image_path = _image_fs_path(image_name)

        caption = f"Карта создана:\n{front}\n— {back_plain}"
        if image_path:
            with image_path.open("rb") as fh:
                await update.message.reply_photo(photo=fh, caption=caption)
        else:
            await update.message.reply_text(caption)
        logger.info(
            "Pipeline finished", extra={"step": "pipeline", "run_id": run_id, "status": "ok"}
        )

    except Exception as e:  # noqa: BLE001
        logger.error(
            "Pipeline finished",
            exc_info=True,
            extra={"step": "pipeline", "run_id": run_id, "status": "error"},
        )
        await update.message.reply_text(f"Ошибка: {e}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    level = os.getenv("LOG_LEVEL")
    if args.verbose:
        level = "DEBUG"
    elif args.quiet:
        level = "WARNING"

    setup_logging(level)
    logger = logging.getLogger(__name__)
    log_effective_settings(logger)
    logger.info("Application starting...")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Telegram polling started", extra={"step": "bot.polling"})
    app.run_polling()


if __name__ == "__main__":  # pragma: no cover
    main()
