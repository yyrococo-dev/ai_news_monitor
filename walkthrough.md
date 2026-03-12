# Gemini LLM 연동 수정 완료

## 수정된 파일

### [summarizer/llm_client.py](file:///Users/hom_mini/dev/ai_news_monitor/summarizer/llm_client.py) — 전면 재작성
- **SDK 교체**: `google.generativeai` (deprecated) → `google-genai` 신규 SDK (`from google import genai`)
- **올바른 API 호출**: `client.models.generate_content(model=..., contents=...)` 패턴 사용
- **모델**: `gemini-2.5-flash` (기본값, `GEMINI_MODEL` 환경변수로 오버라이드 가능)
- **프롬프트 파일 연동**: [prompts/summarize.daily.yaml](file:///Users/hom_mini/dev/ai_news_monitor/prompts/summarize.daily.yaml) 로드 후 실제 프롬프트에 반영
- **불필요 코드 제거**: 잘못된 `google.genai.Client()`, PaLM 모델명, OpenAI 모델명, Jira 연동 코드

### [requirements.txt](file:///Users/hom_mini/dev/ai_news_monitor/requirements.txt)
- `google-generativeai` → `google-genai` 교체
- `PyYAML` 추가 (프롬프트 YAML 파일 파싱용)

### [runner.py](file:///Users/hom_mini/dev/ai_news_monitor/runner.py)
- 시작 시 `load_dotenv()` 호출 추가 ([.env](file:///Users/hom_mini/dev/ai_news_monitor/.env) 키 자동 로딩)
- `--use-llm` 플래그 실제 분기 처리:  `True`면 Gemini API, `False`면 로컬 fallback 요약

## 검증 결과

**LLM 클라이언트 단위 테스트**:
```
INFO: Calling Gemini API (model=gemini-2.5-flash, items=2)
HTTP Request: POST .../gemini-2.5-flash:generateContent "HTTP/1.1 200 OK"
INFO: Gemini API call succeeded
```
→ 한국어 요약 텍스트 정상 반환 ✅

**전체 파이프라인 (`--use-llm --dry-run`)**:
```
INFO: --use-llm flag set: using Gemini API for summarization
INFO: Calling Gemini API (model=gemini-2.5-flash, items=5)
HTTP/1.1 200 OK
INFO: Gemini API call succeeded
Exit code: 0
```
→ RSS 수집 → 중복 제거 → 랭킹 → Gemini 요약 전 구간 정상 동작 ✅

## 실행 방법

```bash
# LLM 사용 (Gemini API 호출)
python runner.py --use-llm

# dry-run (전송 없이 콘솔 출력만)
python runner.py --use-llm --dry-run

# LLM 없이 로컬 fallback 요약
python runner.py --dry-run
```
