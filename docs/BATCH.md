# Batch

Создание нескольких карточек подряд из списка слов.

## Формат данных

`words.csv`:

```csv
word,lang,deck,tag
Hund,de,Deutsch::Lektüre,batch
Haus,de,Deutsch::Lektüre,batch
```

## Скрипт

```python
# batch_make_cards.py
import csv, json, subprocess, sys

with open("words.csv") as f:
    for row in csv.DictReader(f):
        cmd = [
            "python", "cli/make_card.py",
            "--word", row["word"],
            "--lang", row["lang"],
            "--deck", row["deck"],
            "--tag", row["tag"],
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(res.stdout)
        if data.get("error"):
            print(f"{row['word']}: {data['error']}", file=sys.stderr)
        else:
            print(json.dumps(data, ensure_ascii=False))
```

Запуск:

```bash
python batch_make_cards.py > result.jsonl
```

## Пример ответа

```
{"note_id": 123, "front": "Hund", "back": "..."}
{"word": "Haus", "error": "Connection refused"}
```

Строки с полем `error` стоит сохранить отдельно и повторить позже.
