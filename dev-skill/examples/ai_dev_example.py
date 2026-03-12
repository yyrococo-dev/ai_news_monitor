"""
ai-dev 예제 스크립트
- 목적: AI 에이전트(ai-dev)가 기능 개발 작업을 수행할 때 dev-skill 규칙을 참조하고 감사 로그를 남기는 예제입니다.
- 동작:
  1. dev-skill 문서(RULES.md)를 로컬에서 확인(요약)
  2. 간단한 코드 변경(샘플 파일 생성)
  3. 감사 로그 기록
  4. PR 템플릿을 채워 PR 생성(수동 단계 또는 CI 연동)

주의: 실제 PR 생성은 git remote/권한이 필요합니다. 이 스크립트는 예시 목적입니다.
"""

import os
from pathlib import Path
from dev_skill.tools.log_agent_action import log_agent_action

REPO_ROOT = Path(__file__).resolve().parents[2]
DEV_SKILL_DIR = REPO_ROOT / 'dev-skill'

def read_rules():
    r = (DEV_SKILL_DIR / 'RULES.md').read_text(encoding='utf8')
    # 간단 요약(첫 5줄)
    return '\n'.join(r.splitlines()[:10])

def perform_sample_change():
    sample_file = REPO_ROOT / 'dev-skill' / 'examples' / 'sample_change.txt'
    sample_file.write_text('sample change by ai-dev\n')
    return str(sample_file)

if __name__ == '__main__':
    agent_id = 'ai-dev'
    action = 'sample_code_change'
    print('Reading dev-skill rules...')
    print(read_rules())
    changed = perform_sample_change()
    print('Performed change, file:', changed)
    # simple input/output hashes (placeholder)
    input_hash = 'hash-input-sample'
    output_hash = 'hash-output-sample'
    related_issue = None
    log_agent_action(agent_id, action, input_hash=input_hash, output_hash=output_hash, related_issue=related_issue)
    print('Logged agent action to audit table')
