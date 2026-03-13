# ONBOARDING — dev_skill

이 문서는 dev_skill에 포함된 **AI 에이전트 역할**과 **휴먼 인 더 루프(HITL) 정책**을 정리합니다.
모든 에이전트는 [RULES.md](./RULES.md)를 준수해야 하며, 외부 영향 작업은 인간의 명시적 승인이 필요합니다.

---

## AI 에이전트 역할 정의

| 역할 | 책임 | 권한 | 승인 요건 | 검증 기준 |
|---|---|---|---|---|
| **ai-product** | 제품 요구사항 정리, 우선순위 결정, KPI 설정 | Jira 이슈 생성/코멘트 | 정책상 중요한 변경(자동전송 활성화 등)은 ai-product 승인 필요 | PO 승인 코멘트 존재 |
| **ai-data** | 데이터 수집 스펙 제안, 주소 정규화 규칙, 랭킹 파라미터 제안 | DB 읽기/쓰기(개발환경), 스키마 변경 제안 | 스키마 변경은 사람 검토 후 적용 | 정규화 테스트 케이스 통과 |
| **ai-dev** | 코드 변경 제안(PR 생성), 단위테스트 작성, 리팩터 | 브랜치 생성, PR 생성 | PR 병합은 사람 승인 필요(DoD 충족) | lint, unit tests, security scan 통과 |
| **ai-integrator** | 통합 테스트 실행, 외부 연동 검증(모의), 의심 케이스 조사 | 통합 환경(스테이징)에서 테스트 실행 | 통합 실패 시 사람에게 알림 및 티켓 생성 | 통합 스모크 테스트 통과 |
| **ai-qa** | E2E 시나리오 자동 실행, 회귀 테스트, QA 리포트 작성 | 테스트 환경 접근, 테스트 케이스 실행 | 주요 결함은 triage 후 우선순위 지정 | 회귀 테스트 패스율 기준 충족 |
| **ai-ops** | 스테이징 배포 자동화, 모니터링, 이상 감지, 롤백 제안 | 스테이징 자동 배포 실행 | 프로덕션 배포 전 사람 승인 | 스테이징 30분 무에러 |
| **ai-legal** | robots.txt/TOS 자동 검사, PII 탐지, 법무 리스크 초안 작성 | 수집 정책 플래그 설정(권고) | 법적 고위험 케이스는 법무 최종 승인 필요 | robots/TOS 검사 결과 문서화 |
| **ai-notifier** | 요약·알림 초안 생성(Telegram/메일), 알림 스케줄 관리 | 초안 생성, 드라이런 전송 | 실제 전송은 사람 승인 또는 `SCHEDULE_SEND_ENABLE` 정책 필요 | 드라이런 승인 절차 통과 |

---

## 에이전트 파이프라인 흐름

```
ai-product → ai-data → ai-dev → ai-integrator → ai-qa → ai-ops → ai-notifier
                                                               ↑
                                                           ai-legal (수집 허가 검사 — 수집 전 언제든 개입)
```

---

## 휴먼 인 더 루프(HITL)

다음 작업은 사람의 **명시적 승인**(Jira 이슈에 `진행해줘` 코멘트) 없이는 실행하지 않습니다.

- 텔레그램/메일 실제 전송
- 프로덕션 배포
- 대량 크롤링 (robots.txt 미허용 또는 ai-legal 금지 플래그)
- 스키마 변경 적용

---

## 감사 및 기록

모든 AI 에이전트는 `log_agent_action()` 을 호출하여 활동을 기록해야 합니다.

로그 스키마: `agent_id`, `action`, `input_hash`, `output_hash`, `related_issue`, `human_approver`, `ts`

로그 보관: **최소 90일** (RULES.md §2 참고)

---

## 관련 문서

- [RULES.md](./RULES.md) — 운영 룰(승인·감사·위험 차단 등)
- [tools/log_agent_action.py](./tools/log_agent_action.py) — 감사 로그 유틸리티
- [tools/check_robots.py](./tools/check_robots.py) — robots.txt 검사 유틸리티
- [templates/PR_TEMPLATE.md](./templates/PR_TEMPLATE.md) — PR 체크리스트 템플릿

---

_변경 이력_
- 2026-03-12: ROLES.md 내용 통합, 테이블 형식으로 재정리 (SUJI)
- 2026-03-13: Sprint-0 적용 — 파이프라인 상태 관리(pipeline_state), 재시도 정책(ORCH_MAX_RETRIES), HUMAN_INTERVENTION 허들 도입, '재실행해줘' 재시작 흐름 및 Jira 코멘트 기반 알림(플레인 텍스트) 적용. 리포트는 repo/reports/<ISSUE>/에 저장하여 감사 가능하도록 함. (SUJI)

## Sprint-0 변경 요약
다음은 Sprint-0에서 도입된 운영·안전 기능의 요약입니다. 이 항목들은 dev_skill의 Orchestrator와 파이프라인 안전 흐름을 강화합니다.

- pipeline_state 테이블
  - 위치: storage.db
  - 필드: issue_key (PK), state, failure_count, last_error, last_ts, metadata (JSON)
  - 목적: 각 Jira 이슈별 파이프라인 상태를 추적하고, 실패 및 인간 개입 상태를 기록합니다.

- 재시도 정책
  - 환경변수: ORCH_MAX_RETRIES (기본 3), ORCH_RETRY_BACKOFF (선택)
  - 동작: 단계 실패 시 failure_count가 증가하고, failure_count >= ORCH_MAX_RETRIES이면 pipeline_state는 HUMAN_INTERVENTION으로 전환됩니다.

- HUMAN_INTERVENTION 허들
  - 설명: HUMAN_INTERVENTION 상태가 설정되면 Orchestrator는 자동 진행을 중단합니다. 운영자는 Jira 코멘트로 개입을 요청해야 합니다.
  - 재시작 방법: Jira 코멘트에 '재실행해줘' 또는 영어 'resume'을 남기면 webhook 또는 리스너가 이를 감지하여 pipeline_state를 IN_PROGRESS로 변경하고 Orchestrator를 재실행합니다. (권한 검증은 운영 정책에 따라 적용 가능)

- 알림 및 감사
  - 기본 알림 채널: Jira 코멘트(플레인 텍스트) — ADF는 옵션
  - 각 코멘트의 comment_id는 agent_audit 테이블에 기록되어 감사 추적이 가능합니다.
  - Orchestrator 실행 로그 및 요약 리포트는 repo/reports/<ISSUE>/에 저장됩니다.

- 안전 정책
  - 외부 영향 작업(푸시/병합/배포/실제 전송 등)은 '진행해줘' 또는 운영자가 정한 명시적 승인 없이는 실행하지 않습니다.

참고: 이 변경사항은 dev_skill/ONBOARDING_DRAFT.md에 초안으로 먼저 작성되었으며, 내부 검토 후 최종 반영되었습니다.
