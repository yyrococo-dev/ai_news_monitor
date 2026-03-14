---
name: dev_skill
description: OpenClaw skill (draft) packaging of the dev_skill orchestrator, webhook PoC, and developer utilities. Use to reproduce and test the dev pipeline (spec → approve → code → test → report). NOT production-ready: webhook listener requires hardening (WSGI/TLS/IP allowlist/author verification) before public exposure.
---

# dev_skill (OpenClaw skill draft)

요약
- 이 스킬은 dev_skill 레포의 개발·테스트 유틸리티와 오케스트레이터(POC)를 묶어 재현 가능한 개발 환경을 제공합니다. 주 목적은 내부 개발자와 리뷰어가 파이프라인 동작(사양 생성 → 승인 → 코드 생성 → 테스트 → 보고)을 로컬/CI에서 재현하고 검증하는 것입니다.

주요 기능
- 오케스트레이터: 파이프라인 단계(ai-architect, ai-dev-write, ai-dev-review, ai-integrator, ai-qa, ai-ops, ai-legal, ai-notifier)를 드라이런으로 실행하는 스크립트(개발용).
- webhook PoC: Jira 코멘트 기반 approve-spec/reject-spec/resume(재실행) 흐름을 처리하는 웹훅 리스너(Flask PoC).
- 유틸리티: 간단한 ADF 빌더(adf_builder), 실패 분류기(classify_failure), 감사 로그 도구(log_agent_action).
- 샘플 프로젝트: 구구단 PoC(projects/KAN-25) — 사양, 구현, 테스트 포함(Dev pipeline E2E 예시).

포함 항목(초안)
- scripts/ : 실행 가능한 예제 및 주요 스크립트
  - orchestrator.py
  - hooks/webhook_listener.py (PoC)
  - tools/adf_builder.py
  - tools/classify_failure.py
  - tools/log_agent_action.py
  - examples/simulate_sprint1.py, simulate_sprint2.py
- references/ : 사양 및 온보딩 초안
  - reports/KAN-25/spec.md
  - dev_skill/ONBOARDING_DRAFT.md
- tests/ : 샘플 테스트(프로젝트 내)
  - projects/KAN-25/gugudan/tests/

중요한 보안·운영 주의사항(반드시 읽을 것)
- 비밀(토큰/API 키/ngrok authtoken 등)은 절대 스킬에 포함하지 마십시오. 비밀은 GitHub Secrets, OS 키체인, 또는 조직의 Secret Manager를 사용하세요.
- webhook_listener.py는 개발·테스트용 PoC입니다. 운영 배포 전 반드시 다음을 수행하세요:
  - WSGI(gunicorn)으로 실행 및 worker 수/타임아웃 조정
  - TLS(HTTPS) 적용 (nginx 또는 LB에서 TLS 종료)
  - IP allowlist 또는 요청자 검증(Atlassian IP 범위 검증 권장)
  - HMAC 서명 키 롤링 및 비밀 관리
  - 작성자 권한 검증: '재실행' 명령 허용 사용자 목록을 Jira API 또는 그룹으로 제한
- 모든 외부-effect(예: Jira에 코멘트 쓰기, PR 생성, 배포 등)는 기본적으로 dry-run으로 남기고, 명시적 인간 승인('진행해줘') 절차를 요구합니다.

사용 예제(개발자)
- 로컬 드라이런: 리포지토리 루트에서 JIRA_ISSUE_KEY 환경 변수를 설정한 뒤 orchestrator를 실행합니다.
  ```bash
  export JIRA_ISSUE_KEY=KAN-25
  python3 scripts/orchestrator.py
  ```
- webhook 테스트: PoC는 Flask 개발서버로 동작합니다. 운영 전에는 gunicorn/nginx로 마이그레이션하세요.

패키징 안내
- 이 초안은 개발·검증 목적입니다. 스킬 패키징(.skill 생성)은 SKILL.md 검토 후 scripts/package_skill.py로 진행하십시오.

참고 및 링크
- reports/KAN-25/spec.md (ai-architect 샘플 사양)
- dev_skill/ONBOARDING_DRAFT.md (온보딩 초안)

---

*주의: 이 스킬은 초안입니다. 운영 전 하드닝 작업(위 보안 항목)을 반드시 수행하세요.*
