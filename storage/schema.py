import sqlite3
from pathlib import Path
from typing import List, Tuple

DB = Path.home() / 'dev' / 'ai_news_monitor' / 'storage.db'

DEFAULT_OPENCLAW_SOURCES: List[Tuple[str,str]] = [
    ('web','https://docs.openclaw.ai'),
    ('github','https://github.com/openclaw/openclaw'),
    ('web','https://blog.openclaw.ai'),
]

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sent_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        url TEXT UNIQUE,
        title TEXT,
        summary TEXT,
        published_at TEXT,
        fetched_at TEXT,
        sent_at TEXT,
        hash TEXT,
        status TEXT DEFAULT 'PENDING'
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        identifier TEXT UNIQUE,
        last_checked_at TEXT
    )
    ''')
    conn.commit()
    conn.close()


def seed_sources(sources: List[Tuple[str,str]] = None):
    """Idempotently insert sources into the sources table.
    Each source is a tuple (type, identifier).
    """
    if sources is None:
        sources = DEFAULT_OPENCLAW_SOURCES
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for typ, ident in sources:
        try:
            cur.execute('INSERT OR IGNORE INTO sources (type, identifier) VALUES (?, ?)', (typ, ident))
        except Exception:
            pass
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_sources()
    print('db initialized at', DB)
