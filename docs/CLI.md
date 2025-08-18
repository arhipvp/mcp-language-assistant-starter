# CLI

Документы описывают ручной вызов инструмента `lesson.make_card` через простой скрипт.

## Установка

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Перед запуском создайте файл `.env` с адресом AnkiConnect и ключами для внешних сервисов.

## Пример

```bash
python cli/make_card.py --word Hund --lang de --deck "Deutsch::Lektüre" --tag manual
```

Пример вывода:

```json
{
  "note_id": 123,
  "front": "Hund",
  "back": "<div>Перевод: Собака спит</div><div>Satz: Der Hund schläft.</div>",
  "image": ""
}
```

Параметры:

- `--word` — слово для карточки.
- `--lang` — код языка (`de`, `en` и др.).
- `--deck` — целевая колода Anki.
- `--tag` — тег для заметки.
