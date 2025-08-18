from __future__ import annotations

import sqlite3
import time
from pathlib import Path


class TextCache:
    """Simple key-value cache backed by SQLite."""

    def __init__(self, path: str | Path = "var/text_cache.sqlite") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT, created_at INT)"
        )
        self.conn.commit()

    def get(self, key: str) -> str | None:
        cur = self.conn.execute("SELECT v FROM kv WHERE k = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def set(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO kv (k, v, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(k) DO UPDATE SET v=excluded.v, created_at=excluded.created_at",
            (key, value, int(time.time())),
        )
        self.conn.commit()
