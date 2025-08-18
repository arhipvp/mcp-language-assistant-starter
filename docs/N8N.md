# n8n

Импорт и запуск workflow для языка.

## Переменные окружения

Перед запуском n8n определите:

```bash
export TELEGRAM_BOT_TOKEN=...   # токен Telegram бота
export TELEGRAM_CHAT_ID=123456   # ID чата, куда слать сообщения
export MCP_PROXY_URL=http://localhost:8080  # адрес MCP proxy/bridge
```

После этого запустите n8n любым удобным способом (`n8n start`, Docker и т.д.).

## Импорт workflow

1. В интерфейсе n8n выберите **Import from File**.
2. Загрузите файл `workflows/n8n-language-assistant.json` из этого репозитория.
3. Убедитесь, что в ноде **Telegram** используются переменные окружения `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`.
4. Активируйте workflow. Webhook путь указан в ноде `Webhook`.
5. Отправьте POST с JSON `{"word": "Haus"}` на URL webhook — результат придёт в Telegram.
