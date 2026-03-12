import sqlite3
import os
from datetime import datetime
from pathlib import Path

# DB 경로: 환경변수 AUDIT_DB_PATH 또는 repo root storage.db
DB = os.environ.get('AUDIT_DB_PATH', str(Path(__file__).resolve().parents[3] / 'storage.db'))


def init_audit_table(db_path: str = DB):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS agent_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        action TEXT,
        input_hash TEXT,
        output_hash TEXT,
        related_issue TEXT,
        human_approver TEXT,
        ts TEXT
    )
    ''')
    conn.commit()
    conn.close()


def log_agent_action(agent_id, action, input_hash=None, output_hash=None, related_issue=None, human_approver=None, db_path: str = DB):
    """Log an agent action and return the inserted row id."""
    init_audit_table(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO agent_audit (agent_id,action,input_hash,output_hash,related_issue,human_approver,ts) VALUES (?,?,?,?,?,?,?)',
                (agent_id,action,input_hash,output_hash,related_issue,human_approver,ts))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

if __name__ == '__main__':
    init_audit_table()
    print('agent_audit table ready in', DB)
