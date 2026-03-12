#!/usr/bin/env python3
"""
Orchestrator (dry-run) for AI-agent pipeline.

파이프라인 순서:
  ai-product → ai-data → ai-dev → ai-integrator → ai-qa → ai-ops → ai-legal → ai-notifier

- 각 단계는 log_agent_action으로 결과(성공/실패)를 기록합니다.
- 실패 시 파이프라인을 중단하고 감사 로그에 실패를 남긴 뒤 예외를 재발생시킵니다.
- 실제 실행은 각 예제/훅 스크립트와 연결하거나 sessions_spawn/cron으로 확장합니다.
"""

import subprocess
import sys
import os
import time
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / 'tools'))
from log_agent_action import log_agent_action

# jira helper (optional)
try:
    sys.path.append(str(Path(__file__).resolve().parents[2] / '.openclaw' / 'tools'))
except Exception:
    pass
try:
    from jira_helper import jira_post_comment
    from dev_skill.config.templates import detailed_stage_template
except Exception:
    # fallback: try local tools path or disable
    try:
        from jira_helper import jira_post_comment
        from dev_skill.config.templates import detailed_stage_template
    except Exception:
        jira_post_comment = None
        def detailed_stage_template(stage, status, summary, audit_id=None, artifacts=None, next_steps=None):
            parts = [f"(SUJI) 단계: {stage} - 상태: {status}"]
            if summary:
                parts.append(f"요약: {summary}")
            if audit_id:
                parts.append(f"agent_audit id: {audit_id}")
            return "\n".join(parts)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / 'dev_skill' / 'examples'
DB_PATH = REPO_ROOT / 'storage.db'


def _get_last_audit_id(related_issue: str, agent_id: str = 'orchestrator') -> int:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT id FROM agent_audit WHERE related_issue=? AND agent_id=? ORDER BY id DESC LIMIT 1", (related_issue, agent_id))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _post_jira_adf(issue_key: str, stage: str, status: str, summary: str = None, audit_id: int = None, artifacts: list = None):
    """Post a structured ADF comment to Jira summarizing a pipeline stage.

    artifacts: list of (label, url_or_path)
    """
    if not jira_post_comment or not issue_key:
        return False
    body = {
        'body': [
            {
                'type': 'doc',
                'version': 1,
                'content': [
                    {'type': 'paragraph', 'content': [{'type': 'text', 'text': f'(SUJI) 단계: {stage} - 상태: {status}'}]},
                ]
            }
        ]
    }
    if summary:
        body['body'][0]['content'].append({'type': 'paragraph', 'content': [{'type': 'text', 'text': f'요약: {summary}'}]})
    if audit_id:
        body['body'][0]['content'].append({'type': 'paragraph', 'content': [{'type': 'text', 'text': f'agent_audit id: {audit_id}'}]})
    if artifacts:
        for label, path in artifacts:
            body['body'][0]['content'].append({'type': 'paragraph', 'content': [{'type': 'text', 'text': f'{label}: {path}'}]})

    attempts = 0
    last_exc = None
    while attempts < 3:
        try:
            # Try helper first
            jira_post_comment(issue_key, body)
            return True
        except Exception as e:
            last_exc = e
            attempts += 1
            time.sleep(attempts)
    # fallback: post directly via Jira REST using jira.env credentials
    try:
        from pathlib import Path
        import requests
        secrets = Path.home()/'.openclaw'/'secrets'/'jira.env'
        creds = {}
        with open(secrets) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k,v=line.strip().split('=',1); creds[k]=v
        host = creds.get('JIRA_HOST').replace('https://','').replace('http://','').strip('/')
        email = creds.get('JIRA_EMAIL')
        token = creds.get('JIRA_API_TOKEN')
        url = f'https://{host}/rest/api/3/issue/{issue_key}/comment'
        headers={'Content-Type':'application/json'}
        r = requests.post(url, auth=(email,token), json=body, headers=headers, timeout=15)
        r.raise_for_status()
        return True
    except Exception as e:
        log_agent_action('orchestrator', 'jira_post_failed', output_hash=str(e))
        return False


def _step(name: str, fn, jira_issue: str = None):
    """파이프라인 단계를 실행하고 성공/실패를 로그에 남깁니다.

    jira_issue: optional Jira issue key to post step results to.
    """
    print(f'[orchestrator] {name} 시작...')
    try:
        fn()
        # record action
        audit_id = log_agent_action('orchestrator', f'{name}:success', related_issue=jira_issue)
        print(f'[orchestrator] {name} 완료. audit_id={audit_id}')
        # post structured summary to jira if available
        if jira_issue:
            summary_text = f'{name} 단계가 성공적으로 완료되었습니다.'
            artifacts = []
            # include local log path if exists
            log_path = Path('/tmp') / 'orch_flow_run2.log'
            if log_path.exists():
                artifacts.append(('orchestrator_log', str(log_path)))
            # build detailed ADF-like plain summary using template
            try:
                tpl = detailed_stage_template(name, 'success', summary_text, audit_id=audit_id, artifacts=artifacts, next_steps='검토 및 승인 필요시 PR 생성/병합')
            except Exception:
                tpl = summary_text
            _post_jira_adf(jira_issue, name, 'success', summary=tpl, audit_id=audit_id, artifacts=artifacts)
    except Exception as e:
        # record failure
        audit_id = log_agent_action('orchestrator', f'{name}:failed', output_hash=str(e), related_issue=jira_issue)
        print(f'[orchestrator] {name} 실패: {e}', file=sys.stderr)
        if jira_issue:
            _post_jira_adf(jira_issue, name, 'failed', summary=str(e), audit_id=audit_id)
        raise


# ──────────────────────────── 각 에이전트 단계 ────────────────────────────


def run_ai_product():
    """ai-product: 요구사항 정리 및 우선순위 결정 (stub)."""
    # TODO: Jira 이슈 조회 및 제품 스토리 정리 로직 연결
    print('  → ai-product: 요구사항 및 우선순위 확인 (stub)')


def run_ai_data():
    """ai-data: 데이터 수집 스펙 검증 및 스키마 확인 (stub)."""
    # TODO: 스키마 검증, 정규화 테스트 케이스 실행 연결
    print('  → ai-data: 데이터 스키마 및 정규화 확인 (stub)')


def run_ai_dev():
    """ai-dev: 코드 변경 제안 및 단위테스트 실행."""
    dev_script = EXAMPLES_DIR / 'ai_dev_example.py'
    env = os.environ.copy()
    env['PYTHONPATH'] = str(REPO_ROOT)
    subprocess.check_call([sys.executable, str(dev_script)], env=env)


def run_ai_integrator():
    """ai-integrator: 통합 테스트 실행."""
    integrator_script = EXAMPLES_DIR / 'ai_integrator_example.sh'
    subprocess.check_call(['bash', str(integrator_script)])


def run_ai_qa():
    """ai-qa: E2E·회귀 테스트 실행 (stub — 실제 pytest 연결 예정)."""
    # TODO: pytest 또는 QA 잡 실행 연결
    print('  → ai-qa: E2E 시나리오 드라이런 (stub)')


def run_ai_ops():
    """ai-ops: 스테이징 배포 자동화 및 모니터링 (stub)."""
    # TODO: 배포 스크립트 및 모니터링 훅 연결
    print('  → ai-ops: 스테이징 배포 및 모니터링 (stub)')


def run_ai_legal():
    """ai-legal: robots.txt / TOS 검사 및 PII 탐지 (stub)."""
    # TODO: check_robots.py is_allowed()로 수집 대상 전체 검사
    print('  → ai-legal: robots.txt / TOS 검사 (stub)')


def run_ai_notifier():
    """ai-notifier: 알림 초안 생성 및 드라이런 전송 (stub)."""
    # TODO: 텔레그램/메일 드라이런 연결, 실제 전송은 사람 승인 필요
    print('  → ai-notifier: 알림 초안 드라이런 (stub)')


# ─────────────────────────────── 진입점 ───────────────────────────────────

PIPELINE = [
    ('ai-product', run_ai_product),
    ('ai-data',    run_ai_data),
    ('ai-dev',     run_ai_dev),
    ('ai-integrator', run_ai_integrator),
    ('ai-qa',      run_ai_qa),
    ('ai-ops',     run_ai_ops),
    ('ai-legal',   run_ai_legal),
    ('ai-notifier', run_ai_notifier),
]


if __name__ == '__main__':
    print('Orchestrator (dry-run) 시작')
    # Try to read a Jira issue key from env for automatic comments
    jira_issue = os.environ.get('JIRA_ISSUE_KEY')
    for step_name, step_fn in PIPELINE:
        _step(step_name, step_fn, jira_issue=jira_issue)
    print('Orchestrator 완료')
