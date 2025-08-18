# MCP Language Assistant (starter)

Практический стартовый набор для языкового ассистента на базе **Model Context Protocol (MCP)**. Проект объединяет инструменты для:
- получения транскриптов с YouTube
- извлечения словаря с подсказками уровня CEFR
- проверки грамматики через LanguageTool
- генерации аудио с помощью TTS
- автоматического добавления карточек в Anki

## Компоненты

- `app/mcp_server.py` — минимальный MCP‑сервер с зарегистрированными инструментами
- `app/orchestration/pipeline.py` — сборка урока из текста или YouTube
- `app/tools/yt_transcript.py` — загрузка транскриптов
- `app/tools/cefr_level.py` — извлечение словаря и уровней CEFR (использует открытый список частотности)
- `app/tools/grammar.py` — проверка грамматики
- `app/tools/tts.py` — синтез речи через Edge‑TTS
- `app/tools/anki_tool.py` — работа с AnkiConnect
- `app/cli.py` — CLI на Typer

## Быстрый старт

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Пример: построить урок из YouTube и добавить слова в Anki
python -m app.cli build-lesson --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
    --deck "Deutsch::Lektüre" --tag auto-mcp --limit 10 --tts

# Или из произвольного текста
python -m app.cli build-lesson --text "Hallo Welt, wir sprechen freundlich." \
    --deck "Deutsch::Lektüre"
```

Запуск MCP‑сервера:

```bash
python -m app.mcp_server
```

Запуск Telegram-бота:

```bash
export TELEGRAM_BOT_TOKEN=xxx
export OPENROUTER_API_KEY=xxx
export ANKI_CONNECT_URL=http://127.0.0.1:8765
python -m bot.main
```

## Переменные окружения

Создайте файл `.env` и укажите:

```dotenv
LANGUAGETOOL_URL=http://localhost:8010
ANKI_CONNECT_URL=http://127.0.0.1:8765
# Необязательно
DEEPL_API_KEY=...
OPENAI_API_KEY=...
```

## n8n workflow

Готовый workflow лежит в `examples/n8n-word-to-telegram.json`.

1. Запустите n8n, передав переменные окружения:
   - `TELEGRAM_BOT_TOKEN` — токен бота Telegram.
   - `MCP_BASE_URL` — адрес MCP‑прокси или локального stdio‑bridge.
2. В интерфейсе n8n выберите **Import from File** и загрузите `examples/n8n-word-to-telegram.json`.
3. Откройте узлы **Send Photo** и **Send Text** и укажите `chatId` чата, куда слать карточки.
4. Активируйте workflow. Webhook будет доступен по адресу `http://<host>/webhook/word`.
5. Отправьте POST с JSON `{"word": "Haus"}` — в Telegram придёт текст и фото (если найдено).

## Тесты

```bash
pytest
```

---

Сделано для быстрых экспериментов.
