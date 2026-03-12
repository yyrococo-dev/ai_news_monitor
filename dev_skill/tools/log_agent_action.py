import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.expanduser('~'),'dev','ai_news_monitor','storage.db')

def init_audit_table():
    conn = sqlite3.connect(DB)
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


def log_agent_action(agent_id, action, input_hash=None, output_hash=None, related_issue=None, human_approver=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO agent_audit (agent_id,action,input_hash,output_hash,related_issue,human_approver,ts) VALUES (?,?,?,?,?,?,?)',
                (agent_id,action,input_hash,output_hash,related_issue,human_approver,ts))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_audit_table()
    print('agent_audit table ready in', DB)
