# PROJECT SPEC: AI 뉴스 모니터 (수정본)

## 1. 개요
- **목적**: 코딩·AI 관련 변경사항(예: OpenClaw 변경사항), 주요 AI/코딩 뉴스·릴리스·이슈를 매일 오전 08:00에 요약해 지정한 텔레그램 봇으로 전송.
- **범위**: GitHub releases, RSS 피드(블로그/뉴스), 주요 프로젝트 CHANGELOGs, 선택적 웹 스크래핑.
- **실행 방식**: 1회 실행 후 종료되는(One-off) 스크립트를 OS 레벨 스케줄러를 통해 매일 지정된 시간에 트리거하여 리소스를 최적화.

## 2. 요구사항
- **기능 요구사항**
  1) **소스 수집**: GitHub (releases, commits), RSS 피드, 지정 URL 스크래핑 (일시적 네트워크 오류 대비 `tenacity` 라이브러리로 지수 백오프 재시도 적용)
  2) **중복 제거**: 쿼리 파라미터를 제거하는 URL 정규화 로직 적용 후 최근 발송 기록과 비교해 중복 엔트리 차단 (sqlite)
  3) **배치 요약**: 수집한 여러 항목을 모아 하나의 LLM 호출로 요약(비용·쿼터 절약)
  4) **전송**: 텔레그램 봇으로 한 문단 요약 + 원문 링크 전송 (4,096자 제한 대비 Pagination/Truncation 로직 포함)
  5) **스케줄**: 매일 08:00 자동 실행 (OS 스케줄러 또는 CI/CD 파이프라인 활용)
  6) **확장성**: Python `abc` 모듈을 이용한 인터페이스 설계로 향후 Notion/Email 채널 및 신규 소스(Reddit 등) 추가 용이
- **비기능 요구사항**
  - **재현성**: pyenv + virtualenv (3.11) 사용, requirements 고정
  - **보안**: API 키는 `.env`로 관리, `.gitignore`에 포함
  - **신뢰성**: 단계별 상태 관리(Status)를 통한 장애 복구 능력 확보

## 3. 아키텍처(개요)
- **Components**:
  - `core/`: `BaseCollector`, `BaseDeliverer` (추상 클래스/인터페이스)
  - `collectors/`: `github_watcher.py`, `rss_collector.py`, `web_scraper.py` (BaseCollector 상속)
  - `aggregator/`: URL 정규화(normalize), dedupe 로직, batching 전략
  - `summarizer/`: `llm_client.py` (Google Gemini wrapper), `batch_requestor.py`, `local_fallback_summarizer.py` (본문 앞 3문장 추출 등 명시적 룰 적용)
  - `prompts/`: `.yaml` 또는 `.txt` 형태의 외부 프롬프트 템플릿 파일
  - `deliver/`: `telegram_deliver.py` (BaseDeliverer 상속, Pagination 처리), future: `notion_deliver.py`
  - `storage/`: sqlite DB 관리 로직
  - `runner.py`: 1회 실행용 메인 오케스트레이션 스크립트
  - `config/.env`: API 키, 텔레그램 토큰, 소스 목록

## 4. 데이터 플로우 (상태 기반)
1) `collectors`가 소스에서 항목을 가져옴(메타데이터: title, url, published_at, snippet)
2) `aggregator`가 URL 정규화 및 중복 검사 후 신규 항목을 버퍼(DB)에 `PENDING` 상태로 적재
3) `summarizer`가 `PENDING` 항목들을 모아 프롬프트 템플릿과 결합, Gemini API 1회 호출로 요약. 성공 시 상태를 `SUMMARIZED`로 업데이트
4) `deliver`가 `SUMMARIZED` 항목을 Telegram 채널로 전송하고, 성공 시 `DELIVERED`로 상태 업데이트 (실패 시 `FAILED` 처리 및 재시도 대기)

## 5. LLM 연동(세부)
- **공급자**: Google Gemini (`google.genai` 권장)
- **배치 전략**: 하루치 수집 데이터를 하나의 페이로드로 묶어 API 호출 1회로 요청
- **비용/쿼터 대비**: 요청 전 텍스트 길이(토큰)를 계산하여 필요 시 항목을 분할해서 여러 호출 수행
- **에러 처리**: 호출 실패 시 1회 재시도, 최종 실패하면 로컬 룰 기반 요약(본문 3문장 추출)으로 대체 후 알림
- **프롬프트 관리**: 파이썬 코드와 분리하여 `prompts/` 폴더에서 관리, 유지보수성 향상

## 6. DB 설계 (sqlite)
- **Table: sent_items**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `source` TEXT
  - `url` TEXT UNIQUE (정규화된 URL)
  - `title` TEXT
  - `summary` TEXT
  - `published_at` TEXT
  - `fetched_at` TEXT
  - `sent_at` TEXT
  - `hash` TEXT
  - `status` TEXT DEFAULT 'PENDING' (PENDING, SUMMARIZED, DELIVERED, FAILED)
- **Table: sources**
  - `id`, `type` (github/rss/web), `identifier`, `last_checked_at`

## 7. 스케줄링
- **로컬/개발 환경**: 설치된 Homebrew를 활용해 필요한 패키지(DB 도구 등)를 관리하고, macOS 내장 스케줄러인 `launchd`를 통해 `runner.py`를 매일 08:00에 트리거
- **운영 환경**: 서버의 OS `cron` 또는 GitHub Actions의 Scheduled workflow를 사용하여 인프라 유지보수 최소화

## 8. 초기 MVP 구현 범위 (우선순위)
- **1주차(초기)**: 프로젝트 스캐폴딩, 인터페이스(ABC) 정의, pyenv env 세팅, URL 정규화 및 상태값(`status`)이 포함된 sqlite 설계, 기본 collectors(GitHub/RSS), Telegram delivery(Truncation 포함), 로컬 스케줄러 셋업
- **2주차(확장)**: 외부 프롬프트 파일 구조 셋업, Gemini 연동, 배치 토큰 관리, 로컬 대체 요약(Fallback) 로직
- **이후**: CI/CD 배포, Docker, 모니터링, 추가 채널 연동

## 9. 작업 분해(WBS) - 초기 스프린트
- **Task 1**: 스캐폴딩 (레포, 가상환경, `.gitignore`, 인터페이스(ABC) 뼈대 작성, `prompts/` 디렉토리 생성)
- **Task 2**: `collectors/GitHub watcher` 구현 (releases polling + `tenacity` 재시도 적용)
- **Task 3**: `RSS collector` 구현
- **Task 4**: URL 정규화, sqlite DB 초기화 및 상태(Status) 관리 로직 구현
- **Task 5**: Telegram delivery 구현 (메시지 분할/자르기 안전장치 포함) 및 테스트
- **Task 6**: `runner.py` 오케스트레이션 로직 구현 및 로컬 스케줄러 테스트
- **Task 7**: 프롬프트 외부 파일 분리 및 Gemini summarizer 인터페이스 구현
- **Task 8**: 통합 테스트 및 `README` 문서화

## 10. 리스크 및 완화 전략
- **Gemini API 쿼터/비용 초과**: 배치·토큰 분할 로직으로 완화
- **소스 플랫폼 일시 장애**: `tenacity`를 통한 지수 백오프 재시도 처리
- **Telegram 메시지 길이 초과**: Pagination 및 Truncation 로직으로 안전 발송
- **프로세스 중간 실패**: DB 상태값(status) 관리를 통해 실패 지점부터 재시작 가능