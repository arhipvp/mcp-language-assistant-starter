import asyncio
import os
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from app.mcp_tools.lesson import make_card

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DECK = os.getenv("ANKI_DECK", "")
TAG = os.getenv("ANKI_TAG", "")


def _detect_lang(word: str) -> str:
    return "ru" if re.search("[\u0400-\u04FF]", word) else "de"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text or " " in text:
        return
    lang = _detect_lang(text)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: make_card(text, lang, DECK, TAG))
    back_plain = re.sub(r"<[^>]+>", " ", result["back"]).strip()
    await update.message.reply_text(f"Карта создана:\n{result['front']} -> {back_plain}")


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()


if __name__ == "__main__":  # pragma: no cover
    main()
