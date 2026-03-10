import sqlite3
from pathlib import Path

DB = Path.home() / 'dev' / 'ai_news_monitor' / 'storage.db'

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
        identifier TEXT,
        last_checked_at TEXT
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('db initialized at', DB)
