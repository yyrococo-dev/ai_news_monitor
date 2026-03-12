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
except Exception:
    # fallback: try local tools path
    try:
        from jira_helper import jira_post_comment
    except Exception:
        jira_post_comment = None

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / 'dev_skill' / 'examples'


def _post_jira(issue_key: str, text: str, prefer_adf: bool = False):
    """Post a Jira comment. Default is plain-text; ADF is optional (prefer_adf=True).

    Attempt order:
      - jira_helper (text or adf)
      - REST (text or adf)

    Records success/failure into agent_audit with action 'jira_post'. Returns dict with result details.
    """
    if not issue_key:
        return {'ok': False, 'error': 'no_issue_key'}

    attempts = []
    result = {'ok': False, 'attempts': []}

    def record_attempt(method, form, ok, info):
        result['attempts'].append({'method': method, 'form': form, 'ok': ok, 'info': str(info)})

    # helper wrapper
    if jira_post_comment:
        # try preferred form first
        forms = ['adf', 'text'] if prefer_adf else ['text', 'adf']
        for form in forms:
            try:
                if form == 'text':
                    jira_post_comment(issue_key, text)
                else:
                    # build simple ADF wrapper
                    adf = {'body': {'type': 'doc', 'version': 1, 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': text}] }]}}
                    jira_post_comment(issue_key, adf)
                record_attempt('helper', form, True, 'posted')
                log_agent_action('orchestrator', 'jira_post', output_hash=form, related_issue=issue_key)
                result.update({'ok': True, 'method': 'helper', 'form': form})
                return result
            except Exception as e:
                record_attempt('helper', form, False, repr(e))
                time.sleep(1)
    # REST fallback
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
    except Exception as e:
        record_attempt('rest', 'init', False, repr(e))
        log_agent_action('orchestrator', 'jira_post_failed', output_hash=str(e), related_issue=issue_key)
        return result

    forms = ['adf', 'text'] if prefer_adf else ['text', 'adf']
    for form in forms:
        try:
            url = f'https://{host}/rest/api/3/issue/{issue_key}/comment'
            headers = {'Content-Type': 'application/json'}
            if form == 'text':
                payload = {'body': text}
            else:
                payload = {'body': {'type': 'doc', 'version': 1, 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': text}] }]}}
            r = requests.post(url, auth=(email, token), json=payload, headers=headers, timeout=15)
            if r.ok:
                record_attempt('rest', form, True, f'status:{r.status_code}')
                try:
                    cid = r.json().get('id')
                except Exception:
                    cid = None
                log_agent_action('orchestrator', 'jira_post', output_hash=form, related_issue=issue_key)
                result.update({'ok': True, 'method': 'rest', 'form': form, 'comment_id': cid, 'status_code': r.status_code})
                return result
            else:
                record_attempt('rest', form, False, f'status:{r.status_code} body:{r.text[:200]}')
        except Exception as e:
            record_attempt('rest', form, False, repr(e))
            time.sleep(1)

    # all attempts failed
    log_agent_action('orchestrator', 'jira_post_failed', output_hash=str(result), related_issue=issue_key)
    return result


def _step(name: str, fn, jira_issue: str = None):
    """파이프라인 단계를 실행하고 성공/실패를 로그에 남깁니다.

    jira_issue: optional Jira issue key to post step results to.
    """
    print(f'[orchestrator] {name} 시작...')
    try:
        fn()
        log_agent_action('orchestrator', f'{name}:success')
        print(f'[orchestrator] {name} 완료.')
        # post summary to jira if available
        if jira_issue:
            text = f"(SUJI) {name} 완료. 상태: success."
            _post_jira(jira_issue, text)
    except Exception as e:
        log_agent_action('orchestrator', f'{name}:failed', output_hash=str(e))
        print(f'[orchestrator] {name} 실패: {e}', file=sys.stderr)
        if jira_issue:
            text = f"(SUJI) {name} 실패. 예외: {e}"
            _post_jira(jira_issue, text)
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
