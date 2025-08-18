import sqlite3

from app.cache.text_cache import TextCache


def test_put_get(tmp_path):
    db = tmp_path / "cache.sqlite"
    cache = TextCache(db)
    key = "abc"
    value = "result"

    assert cache.get(key) is None
    cache.set(key, value)

    # reopen to ensure data persisted
    cache2 = TextCache(db)
    assert cache2.get(key) == value


def test_idempotent(tmp_path):
    db = tmp_path / "cache.sqlite"
    cache = TextCache(db)
    key = "abc"
    value = "result"

    cache.set(key, value)
    cache.set(key, value)

    assert cache.get(key) == value

    # ensure single row in table
    conn = sqlite3.connect(db)
    count = conn.execute("SELECT COUNT(*) FROM kv").fetchone()[0]
    conn.close()
    assert count == 1
