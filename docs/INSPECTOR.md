# Inspector

Инструмент для взаимодействия с MCP через браузер.

## Установка

1. Установите Node.js.
2. Установите пакет инспектора:

```bash
npm install -g @modelcontextprotocol/inspector
```

## Запуск и подключение к локальному серверу

Следующая команда одновременно поднимет локальный MCP‑сервер через `stdio` и откроет Inspector:

```bash
npx @modelcontextprotocol/inspector --stdio "python -m app.mcp_server"
```

Откройте адрес из вывода (обычно `http://localhost:5173`).

## Примеры вызовов

Через веб‑интерфейс можно вызывать зарегистрированные инструменты:

- **server.health** — проверка окружения и доступности зависимостей.
- **lesson.make_card** с JSON‑аргументами:

```json
{"word": "Haus", "lang": "de", "deck": "Deutsch::Lektüre", "tag": "demo"}
```

После выполнения в Anki появится новая карточка (если запущен AnkiConnect).
