# WBS - AI 뉴스 모니터 (working board)

운영 규칙: 코드 개발 시 모든 작업은 이 WBS 또는 Jira(KAN) 이슈에 등록하고, 작업 완료 시 해당 항목을 `DONE`으로 체크합니다. 누락을 방지하기 위해 PR/커밋 메시지에 WBS 항목 번호 또는 Jira 이슈 키를 포함하세요.

## Sprint 1 - 초기 (1주차)
- [x] 1.1 스캐폴딩: 리포지토리, 가상환경, .gitignore, README 초안
- [x] 1.2 Base interfaces: core/BaseCollector, core/BaseDeliverer (ABC)
- [x] 1.3 storage: sqlite 초기화 스크립트 + storage/schema.py (sent_items, sources 테이블)
- [x] 1.4 collectors: collectors/github_watcher.py (releases polling, tenacity 적용)  
- [x] 1.5 collectors: collectors/rss_collector.py (RSS 파서, feedparser 사용)
- [x] 1.6 aggregator: URL 정규화, dedupe, PENDING 상태 로직
- [x] 1.7 runner.py: 오케스트레이션(한 번 실행 후 종료형) + 로컬 실행 가이드
- [x] 1.8 deliver: deliver/telegram_deliver.py (message truncation/pagination)
- [ ] 1.9 통합 테스트: 수집 → 요약(fallback) → 전송 시나리오 실행
- [ ] 1.10 sources: OpenClaw 공식 도메인/레포(예: docs.openclaw.ai, github.com/openclaw/openclaw) 기본 소스 목록에 추가 및 config/.env.example 반영

## Sprint 2 - 확장 (2주차)
- [ ] 2.1 prompts/: 외부 프롬프트 파일 구조(.yaml/.txt)
- [ ] 2.2 summarizer: llm_client.py (Gemini wrapper stub) + batch_requestor.py
- [ ] 2.3 fallback summarizer: local_fallback_summarizer.py (본문 앞 3문장 추출)
- [ ] 2.4 scheduler: launchd / cron 예제 및 runner cron 등록 스크립트
- [ ] 2.5 docs: README 상세(설치/운영/온보딩)

## Ops / Monitoring
- [ ] O1 quota_monitor integration for summary jobs
- [ ] O2 logging and error reporting (rotating logs, Sentry placeholder)

---

Notes:
- 각 항목에 대해 작업 시작 시 담당자(Assignee)와 예상 소요시간(예: 2h, 1d)을 주석으로 추가하세요.
- 완료 시 체크박스 앞에 날짜와 커밋/PR 링크 또는 Jira 이슈 키를 덧붙입니다.

(파일: dev/ai_news_monitor/WBS.md)
