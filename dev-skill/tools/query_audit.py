import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.expanduser('~'),'dev','ai_news_monitor','storage.db')

def recent_audit(limit=50):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT id,agent_id,action,related_issue,human_approver,ts FROM agent_audit ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

if __name__ == '__main__':
    rows = recent_audit(20)
    for r in rows:
        print(r)
