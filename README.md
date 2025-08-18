
# MCP Language Assistant (starter)

A practical starter for a language-learning assistant built around **Model Context Protocol (MCP)** concepts and easily usable from tools like n8n. The aim is to orchestrate agents/tools for:
- Getting transcripts from videos (YouTube)
- Extracting vocabulary + CEFR tagging
- Grammar feedback (LanguageTool)
- Generating TTS for listening practice
- Creating Anki cards automatically (AnkiConnect)

> This is a scaffold: minimal working pieces + clear TODOs to wire a real MCP server (Anthropic MCP).

## Components

- `app/mcp_server.py` — placeholder MCP server entry (wire real MCP here)
- `app/orchestration/pipeline.py` — simple pipeline orchestrator (works without MCP)
- `app/tools/yt_transcript.py` — fetch YouTube transcripts (uses `youtube-transcript-api`)
- `app/tools/anki_tool.py` — push cards via AnkiConnect
- `app/tools/cefr_level.py` — naive CEFR estimator (stub)
- `app/tools/grammar.py` — LanguageTool integration (local or remote URL)
- `app/tools/tts.py` — TTS interface (stub; plug in Coqui TTS / Piper / Edge-TTS)
- `app/cli.py` — Typer CLI: run end-to-end: URL -> vocab -> grammar -> Anki

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# 1) Optional: run local LanguageTool
# docker run -p 8010:8010 -e LANGUAGETOOL_LANGUAGE_MODEL=/ngrams #   silviof/docker-languagetool

# 2) Ensure Anki is running and AnkiConnect is installed (port 8765)

# 3) Extract and push 10 words from a YouTube URL into Anki:
python -m app.cli youtube-to-anki   --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"   --deck "Deutsch::Lektüre"   --tag "auto-mcp"   --limit 10
```

## Environment

Copy `.env.example` to `.env` and adjust:

```
LANGUAGETOOL_URL=http://localhost:8010
ANKI_CONNECT_URL=http://127.0.0.1:8765
```

## Roadmap to full MCP

1. Replace `app/mcp_server.py` with a real MCP server (Anthropic's SDK).
2. Register tools:
   - `transcript.get(url)`
   - `vocab.extract(text, limit)`
   - `grammar.check(text[, level])`
   - `tts.speak(text, voice)`
   - `anki.add_note(front, back, deck, tags)`
3. Expose a composite tool `lesson.build(url|text)` that runs the pipeline.
4. Add auth/ratelimiting, logging, and tests.

---

Made for quick hacking and iteration.
