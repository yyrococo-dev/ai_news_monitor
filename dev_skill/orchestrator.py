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


def _post_jira(issue_key: str, text: str, prefer_adf: bool = True):
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
                    # build ADF wrapper using adf_builder if available
                    try:
                        from dev_skill.tools.adf_builder import build_doc
                        adf_doc = build_doc([text])
                        adf = {'body': adf_doc}
                    except Exception:
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
                try:
                    from dev_skill.tools.adf_builder import build_doc
                    adf_doc = build_doc([text])
                    payload = {'body': adf_doc}
                except Exception:
                    payload = {'body': {'type': 'doc', 'version': 1, 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': text}] }]}}
            r = requests.post(url, auth=(email, token), json=payload, headers=headers, timeout=15)
            if r.ok:
                record_attempt('rest', form, True, f'status:{r.status_code}')
                try:
                    cid = r.json().get('id')
                except Exception:
                    cid = None
                # record the post action and return comment id
                log_agent_action('orchestrator', 'jira_post', output_hash=form, related_issue=issue_key, db_path=str(REPO_ROOT/'storage.db'))
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


import sqlite3
import json

def _ensure_pipeline_table(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_state (
            issue_key TEXT PRIMARY KEY,
            state TEXT,
            failure_count INTEGER DEFAULT 0,
            last_error TEXT,
            last_ts TEXT,
            metadata TEXT
        )
        ''')
        conn.commit()
        conn.close()
    except Exception:
        pass


def _get_pipeline_state(db_path: str, issue_key: str):
    _ensure_pipeline_table(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT state,failure_count,last_error,last_ts,metadata FROM pipeline_state WHERE issue_key=?', (issue_key,))
    row = cur.fetchone()
    conn.close()
    if row:
        state, failure_count, last_error, last_ts, metadata = row
        meta = json.loads(metadata) if metadata else {}
        return {'state': state, 'failure_count': failure_count, 'last_error': last_error, 'last_ts': last_ts, 'metadata': meta}
    else:
        return None


def _set_pipeline_state(db_path: str, issue_key: str, state: str, error: str = None, metadata: dict = None):
    _ensure_pipeline_table(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    import datetime
    ts = datetime.datetime.utcnow().isoformat()
    meta_json = json.dumps(metadata or {})
    cur.execute('INSERT INTO pipeline_state (issue_key,state,failure_count,last_error,last_ts,metadata) VALUES (?,?,?,?,?,?) ON CONFLICT(issue_key) DO UPDATE SET state=excluded.state, last_error=excluded.last_error, last_ts=excluded.last_ts, metadata=excluded.metadata', (issue_key, state, 0, error, ts, meta_json))
    conn.commit()
    conn.close()


def _incr_failure(db_path: str, issue_key: str, last_error: str = None):
    _ensure_pipeline_table(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT failure_count FROM pipeline_state WHERE issue_key=?', (issue_key,))
    row = cur.fetchone()
    if row:
        fc = row[0] + 1
        import datetime
        ts = datetime.datetime.utcnow().isoformat()
        cur.execute('UPDATE pipeline_state SET failure_count=?, last_error=?, last_ts=? WHERE issue_key=?', (fc, last_error, ts, issue_key))
    else:
        import datetime
        ts = datetime.datetime.utcnow().isoformat()
        cur.execute('INSERT INTO pipeline_state (issue_key,state,failure_count,last_error,last_ts,metadata) VALUES (?,?,?,?,?,?)', (issue_key, 'DEVELOPMENT', 1, last_error, ts, json.dumps({})))
        fc = 1
    conn.commit()
    conn.close()
    return fc


def _build_plain_comment(stage: str, status: str, summary: str = None, audit_id: int = None, artifacts: list = None):
    lines = [f"(SUJI) 단계: {stage} — 상태: {status}"]
    if summary:
        lines.append(f"요약: {summary}")
    if audit_id:
        lines.append(f"agent_audit id: {audit_id}")
    if artifacts:
        lines.append("주요 아티팩트:")
        for label, path in artifacts:
            lines.append(f"- {label}: {path}")
    from datetime import datetime
    lines.append(f"보고시간: {datetime.utcnow().isoformat()}Z")
    return "\n".join(lines)


def _step(name: str, fn, jira_issue: str = None):
    """파이프라인 단계를 실행하고 성공/실패를 로그에 남깁니다.

    jira_issue: optional Jira issue key to post step results to.
    """
    print(f'[orchestrator] {name} 시작...')
    try:
        fn()
        # record action and get audit id (use canonical storage.db path)
        audit_id = log_agent_action('orchestrator', f'{name}:success', related_issue=jira_issue, db_path=str(REPO_ROOT/'storage.db'))
        print(f'[orchestrator] {name} 완료. audit_id={audit_id}')
        # reset failure count on success
        if jira_issue:
            try:
                _set_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue, 'IN_PROGRESS', metadata={'last_success': name})
            except Exception:
                pass
        # post summary to jira if available
        if jira_issue:
            summary = f"{name} 단계가 성공적으로 완료되었습니다."
            artifacts = []
            # include orchestrator run log if present
            log_path = Path('/tmp') / 'orch_kan22_run_fix.log'
            if log_path.exists():
                artifacts.append(('orchestrator_log', str(log_path)))
            text = _build_plain_comment(name, 'success', summary=summary, audit_id=audit_id, artifacts=artifacts)
            res = _post_jira(jira_issue, text)
            try:
                cid = None
                if isinstance(res, dict):
                    cid = res.get('comment_id')
                if cid:
                    log_agent_action('orchestrator', 'jira_comment_posted', output_hash=str(cid), related_issue=jira_issue, db_path=str(REPO_ROOT/'storage.db'))
            except Exception:
                pass
    except Exception as e:
        # increment failure counter and possibly trigger HUMAN_INTERVENTION
        try:
            fc = _incr_failure(str(REPO_ROOT/'storage.db'), jira_issue, last_error=str(e)) if jira_issue else None
        except Exception:
            fc = None
        audit_id = log_agent_action('orchestrator', f'{name}:failed', output_hash=str(e), related_issue=jira_issue, db_path=str(REPO_ROOT/'storage.db'))
        print(f'[orchestrator] {name} 실패: {e}', file=sys.stderr)
        # classify failure and decide transition
        try:
            from dev_skill.tools.classify_failure import classify_failure
            clf = classify_failure(str(e))
        except Exception:
            clf = {'label':'other','score':0.0,'reason':'classifier_error'}
        try:
            max_retries = int(os.environ.get('ORCH_MAX_RETRIES', '3'))
        except Exception:
            max_retries = 3
        # If exceeded retries, set HUMAN_INTERVENTION (with classifier context) and notify
        if fc and fc >= max_retries:
            try:
                _set_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue, 'HUMAN_INTERVENTION', error=str(e), metadata={'failed_step': name, 'failure_count': fc, 'classify': clf})
            except Exception:
                pass
            # suggest automatic rollback or transition based on classifier if enabled
            auto_rb = os.environ.get('ORCH_AUTO_ROLLBACK','true').lower() in ('1','true','yes')
            action_taken = None
            if auto_rb and clf.get('score',0.0) >= float(os.environ.get('ORCH_CLASSIFY_CONF_THRESHOLD','0.6')):
                lbl = clf.get('label')
                if lbl == 'code':
                    # propose/perform transition to DEVELOPMENT
                    _set_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue, 'DEVELOPMENT', metadata={'auto_from': 'HUMAN_INTERVENTION','reason': clf})
                    log_agent_action('orchestrator','auto_transition',output_hash='DEVELOPMENT',related_issue=jira_issue,db_path=str(REPO_ROOT/'storage.db'))
                    action_taken = 'auto_development'
                elif lbl == 'design':
                    _set_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue, 'DESIGN_REVIEW', metadata={'auto_from':'HUMAN_INTERVENTION','reason':clf})
                    log_agent_action('orchestrator','auto_transition',output_hash='DESIGN_REVIEW',related_issue=jira_issue,db_path=str(REPO_ROOT/'storage.db'))
                    action_taken = 'auto_design'
                elif lbl == 'data':
                    _set_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue, 'DATA_INVESTIGATION', metadata={'auto_from':'HUMAN_INTERVENTION','reason':clf})
                    log_agent_action('orchestrator','auto_transition',output_hash='DATA_INVESTIGATION',related_issue=jira_issue,db_path=str(REPO_ROOT/'storage.db'))
                    action_taken = 'auto_data'
            # notify via jira comment (include resume guidance and classifier)
            if jira_issue:
                notify_text = _build_plain_comment(name, 'human_intervention', summary=f'최대 재시도({max_retries}) 초과 — 인간 개입 필요: {e}', audit_id=audit_id, artifacts=None)
                notify_text = notify_text + "\n\n안내: 이 이슈에 '재실행해줘' 라는 코멘트를 남기면 Orchestrator가 HUMAN_INTERVENTION을 해제하고 파이프라인을 재시작합니다. (영어: 'resume')"
                notify_text = notify_text + f"\n\n분류: {clf.get('label')} (score={clf.get('score')}) — {clf.get('reason')}"
                if action_taken:
                    notify_text = notify_text + f"\n\n자동 조치: {action_taken} (상세는 agent_audit 참조)"
                _post_jira(jira_issue, notify_text)
                log_agent_action('orchestrator', 'human_intervention_notified', output_hash=str(fc), related_issue=jira_issue, db_path=str(REPO_ROOT/'storage.db'))
        else:
            # set state to error/development
            try:
                _set_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue, 'ERROR', error=str(e), metadata={'failed_step': name, 'failure_count': fc})
            except Exception:
                pass
            if jira_issue:
                text = _build_plain_comment(name, 'failed', summary=str(e), audit_id=audit_id)
                res = _post_jira(jira_issue, text)
                try:
                    cid = None
                    if isinstance(res, dict):
                        cid = res.get('comment_id')
                    if cid:
                        log_agent_action('orchestrator', 'jira_comment_posted', output_hash=str(cid), related_issue=jira_issue, db_path=str(REPO_ROOT/'storage.db'))
                except Exception:
                    pass
        raise


# ──────────────────────────── 각 에이전트 단계 ────────────────────────────


def run_ai_product():
    """ai-product: 요구사항 정리 및 우선순위 결정 (stub)."""
    print('  → ai-product: 요구사항 및 우선순위 확인 (stub)')


def run_ai_data():
    """ai-data: 데이터 수집 스펙 검증 및 스키마 확인 (stub)."""
    print('  → ai-data: 데이터 스키마 및 정규화 확인 (stub)')


def run_ai_architect():
    """ai-architect: 기술 설계서(spec.md), OpenAPI stub, ERD 생성 및 reports/<ISSUE>/spec.md 저장."""
    try:
        jira_issue = os.environ.get('JIRA_ISSUE_KEY')
        reports_dir = REPO_ROOT / 'reports' / (jira_issue or 'LOCAL')
        reports_dir.mkdir(parents=True, exist_ok=True)
        spec_path = reports_dir / 'spec.md'
        # simple spec stub
        template = (REPO_ROOT / 'dev_skill' / 'templates' / 'spec_template.md')
        if template.exists():
            content = template.read_text()
        else:
            content = f"# Technical Spec for {jira_issue or 'LOCAL'}\n\n- OpenAPI: stub\n- ERD: placeholder\n"
        spec_path.write_text(content)
        print(f'  → ai-architect: spec generated at {spec_path}')
        # set pipeline state to DESIGN_REVIEW
        try:
            _set_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue, 'DESIGN_REVIEW', metadata={'spec_path': str(spec_path)})
        except Exception:
            pass
        # post Jira comment asking for approve-spec
        if jira_issue:
            text = _build_plain_comment('ai-architect', 'design_ready', summary='Tech spec 생성 완료. 검토 후 Jira에 `approve-spec` 또는 `reject-spec` 코멘트를 남겨주세요.', artifacts=[('spec', str(spec_path))])
            _post_jira(jira_issue, text)
    except Exception as e:
        print('ai-architect failed', e)
        raise


def run_ai_dev_write():
    """ai-dev-write: 생성된 설계(승인 후) 기반으로 코드 변경 초안을 생성(시뮬레이션)."""
    jira_issue = os.environ.get('JIRA_ISSUE_KEY')
    workdir = REPO_ROOT / 'projects' / (jira_issue or 'LOCAL')
    workdir.mkdir(parents=True, exist_ok=True)
    patch_file = workdir / 'proposed_change.patch'
    patch_file.write_text('# patch stub\n# changes proposed by ai-dev-write')
    print(f'  → ai-dev-write: patch created at {patch_file}')
    # record action
    log_agent_action('ai-dev-write', 'proposed_patch', output_hash=str(patch_file), related_issue=jira_issue, db_path=str(REPO_ROOT/'storage.db'))


def run_ai_dev_review():
    """ai-dev-review: 정적분석(시뮬레이션) 및 리뷰 코멘트 생성. PR은 생성하되 병합은 사람 승인 필요."""
    jira_issue = os.environ.get('JIRA_ISSUE_KEY')
    print('  → ai-dev-review: running static analysis (simulated)')
    # simulate checks
    findings = ['lint: ok', 'mypy: ok', 'security: low-risk']
    summary = '\n'.join(findings)
    # post review summary to jira
    if jira_issue:
        text = _build_plain_comment('ai-dev-review', 'review_complete', summary=summary)
        _post_jira(jira_issue, text)
    log_agent_action('ai-dev-review', 'review_complete', output_hash=summary, related_issue=jira_issue, db_path=str(REPO_ROOT/'storage.db'))


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
    ('ai-architect', run_ai_architect),
    ('ai-dev-write', run_ai_dev_write),
    ('ai-dev-review', run_ai_dev_review),
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
        # check pipeline state for this issue; if HUMAN_INTERVENTION, stop further automated progress
        if jira_issue:
            try:
                ps = _get_pipeline_state(str(REPO_ROOT/'storage.db'), jira_issue)
                if ps and ps.get('state') == 'HUMAN_INTERVENTION':
                    print(f'[orchestrator] {jira_issue} in HUMAN_INTERVENTION — automated progress halted. Awaiting manual resolution.')
                    break
            except Exception:
                pass
        _step(step_name, step_fn, jira_issue=jira_issue)
    print('Orchestrator 완료')
