import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

import app as core

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DECK = os.environ["ANKI_DECK"]
TAG = os.environ["ANKI_TAG"]

CYRILLIC_RE = re.compile("[\u0400-\u04FF]")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = (update.message.text or "").strip()
    lang = "ru" if CYRILLIC_RE.search(word) else "en"
    try:
        card = core.make_card(word, lang, DECK, TAG)  # type: ignore[attr-defined]
        if isinstance(card, dict):
            front = card.get("front", word)
            image_path = card.get("image") or card.get("image_path")
        else:
            front = str(card)
            image_path = None
        marker = "картинка есть" if image_path else "картинки нет"
        reply = f"{front}\n\nдобавлено ({marker})"
        if image_path:
            with open(image_path, "rb") as fh:
                await update.message.reply_photo(photo=fh, caption=reply)
        else:
            await update.message.reply_text(reply)
    except Exception as e:  # noqa: BLE001
        await update.message.reply_text(f"ошибка: {e}")


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_polling()


if __name__ == "__main__":
    main()
