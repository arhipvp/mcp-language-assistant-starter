# GenAPI

Краткое руководство по использованию сервиса [gen-api.ru](https://gen-api.ru) для генерации изображений.

## Режимы работы
GenAPI поддерживает три стратегии получения результата:

- **Long‑poll** – создаём задачу и регулярно опрашиваем `GET /tasks/{id}` до получения `status=done`.
- **Callback** – при создании задачи передаём `callback_url`; сервис отправит результат POST‑запросом.
- **Sync** – параметр `mode=sync` заставит API дождаться готового изображения и вернуть его сразу.

## Настройка окружения
В корне проекта создайте файл `.env` со следующими переменными:

```env
GENAPI_URL=https://api.gen-api.ru/v1
GENAPI_API_KEY=
GENAPI_MODEL=gpt-image-1
DEBUG=0
```

`GENAPI_URL` и `GENAPI_MODEL` имеют значения по умолчанию, токен нужно получить в личном кабинете.

## Генерация одной картинки
Простейший способ получить изображение – отправить синхронный запрос через `curl`:

```bash
curl -H "Authorization: Bearer $GENAPI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-image-1","prompt":"кот в космосе"}' \
     "$GENAPI_URL/images/sync" > out.png
```

`out.png` будет содержать готовую картинку.

## Отладка
- Установите `DEBUG=1` в `.env` для подробных логов.
- Проверяйте баланс: `curl -H "Authorization: Bearer $GENAPI_API_KEY" "$GENAPI_URL/balance"`.
- Состояние задачи: `curl -H "Authorization: Bearer $GENAPI_API_KEY" "$GENAPI_URL/tasks/<id>"`.
- При ошибке смотрите поля `code` и `message` в ответе – на сайте есть расшифровка.

Указывайте модель `gpt-image-1` – её поддерживает сервис по умолчанию.
