# dev_skill

이 스킬은 우리 조직의 개발·검증·배포 규칙과 AI 역할(Agent) 매핑을 표준화하기 위한 개발 스킬입니다. 이 스킬에 포함된 문서와 도구는 모든 개발 활동(특히 AI가 수행하는 자동화 작업)에 대해 일관된 정책·감사·승인 플로우를 제공합니다.

주요 내용
- ONBOARDING.md: AI 에이전트 역할 정의(ai-product, ai-data, ai-architect, ai-dev, ai-integrator, ai-qa, ai-ops, ai-legal, ai-notifier) 및 책임, HITL 정책
- RULES.md: 운영 룰(승인·감사·위험 차단 등)
- orchestrator.py: AI 에이전트 파이프라인 실행기 (단계 포함: ai-architect → ai-dev-write → ai-dev-review → ai-integrator → ai-qa → ...; dry-run 지원)
- tools/: 감사 로그 헬퍼(log_agent_action.py), robots.txt 검사(check_robots.py), 로그 조회(query_audit.py)
- templates/: PR/Issue 템플릿(체크리스트 포함)
- hooks/: Jira 승인 이벤트 리스너 등 외부 연동 훅
- WBS.md: Orchestrator 개선 WBS 및 Sprint 계획(추가됨)

사용 방법
1. 스킬을 읽고 운영 룰(RULES.md)을 숙지합니다.
2. 새로운 자동화는 반드시 이 스킬의 규칙을 따르며, 외부 영향 작업은 명시적 승인이 필요합니다.
3. AUDIT_DB_PATH 환경변수로 감사 로그 DB 경로를 지정할 수 있습니다 (미설정 시 프로젝트 루트의 storage.db 사용).

변경 및 개선 요약
- ai-architect 역할 추가 제안: PRD → Tech Spec(OpenAPI/ERD/아키다이어그램) 생성, 사람 승인 허들
- Maker/Checker 분리: ai-dev를 작성/검토 단계로 나누어 PR 승인권한과 책임 분리
- 장애 루프 처리: MAX_RETRIES (기본 3) 이상 실패 시 HUMAN_INTERVENTION으로 전이하고 ai-notifier로 알림 발송
- 코멘트 전송: 기본 플레인 텍스트(ADF는 옵션), 각 코멘트의 comment_id를 agent_audit에 기록함

참고: 자세한 WBS와 단계별 작업은 dev_skill/WBS.md를 참고하세요.
