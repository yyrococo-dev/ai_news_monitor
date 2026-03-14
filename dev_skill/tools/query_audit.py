"""
query_audit.py — 감사 로그 조회 유틸리티

주요 기능:
  - recent_audit(limit): 최근 감사 로그 조회
  - query_by_agent(agent_id, limit): 특정 에이전트 로그 조회
"""

import sqlite3
import os
from pathlib import Path

# DB 경로: 환경변수 AUDIT_DB_PATH → 없으면 프로젝트 루트의 storage.db
DB = os.environ.get(
    'AUDIT_DB_PATH',
    str(Path(__file__).resolve().parents[3] / 'storage.db')
)


def recent_audit(limit: int = 50, db_path: str = DB) -> list:
    """최근 감사 로그를 최신순으로 반환합니다."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        'SELECT id, agent_id, action, related_issue, human_approver, ts '
        'FROM agent_audit ORDER BY id DESC LIMIT ?',
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def query_by_agent(agent_id: str, limit: int = 50, db_path: str = DB) -> list:
    """특정 에이전트의 감사 로그를 최신순으로 반환합니다."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        'SELECT id, agent_id, action, related_issue, human_approver, ts '
        'FROM agent_audit WHERE agent_id = ? ORDER BY id DESC LIMIT ?',
        (agent_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        rows = query_by_agent(sys.argv[1])
        print(f'--- {sys.argv[1]} 감사 로그 ---')
    else:
        rows = recent_audit(20)
        print('--- 최근 감사 로그 ---')
    for r in rows:
        print(r)
