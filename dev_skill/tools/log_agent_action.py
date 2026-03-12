import sqlite3
import os
from datetime import datetime
from pathlib import Path

# DB 경로: 환경변수 AUDIT_DB_PATH → 없으면 프로젝트 루트의 storage.db
DB = os.environ.get(
    'AUDIT_DB_PATH',
    str(Path(__file__).resolve().parents[3] / 'storage.db')
)


def init_audit_table(db_path: str = DB):
    """agent_audit 테이블을 생성합니다 (멱등 — 이미 존재하면 무시)."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS agent_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        action TEXT NOT NULL,
        input_hash TEXT,
        output_hash TEXT,
        related_issue TEXT,
        human_approver TEXT,
        ts TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()


def log_agent_action(
    agent_id: str,
    action: str,
    input_hash: str = None,
    output_hash: str = None,
    related_issue: str = None,
    human_approver: str = None,
    db_path: str = DB,
):
    """에이전트 액션을 감사 로그 DB에 기록합니다.

    Args:
        agent_id: 에이전트 식별자 (예: 'ai-dev')
        action: 수행한 액션 명칭
        input_hash: 입력 데이터 해시 (선택)
        output_hash: 출력 데이터 해시 (선택)
        related_issue: 관련 Jira 이슈 키 (선택)
        human_approver: 승인한 사람 ID (선택)
        db_path: SQLite DB 경로 (기본값: AUDIT_DB_PATH 환경변수 또는 프로젝트 루트)
    """
    init_audit_table(db_path)  # 테이블 없으면 자동 생성 (멱등)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat()
    cur.execute(
        'INSERT INTO agent_audit '
        '(agent_id, action, input_hash, output_hash, related_issue, human_approver, ts) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (agent_id, action, input_hash, output_hash, related_issue, human_approver, ts),
    )
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


if __name__ == '__main__':
    init_audit_table()
    print('agent_audit table ready in', DB)
