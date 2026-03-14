# 구구단(샘플) — 아키텍처 사양

목적: dev_skill 파이프라인 E2E 검증용 샘플 프로젝트. 1..2단 구구단 출력 PoC.

런타임/언어: Python 3.8+

프로젝트 구조:
- projects/KAN-25/gugudan/
  - README.md
  - gugudan.py (엔트리포인트)
  - gugudan/core.py (비즈니스 로직)
  - tests/test_core.py (pytest)
  - requirements.txt

공개 함수 인터페이스:
- generate_dan(dan: int) -> list[str]
  - 설명: dan에 대한 1..9 형식의 문자열 리스트 반환
- build_full_output(max_dan: int = 2) -> str
  - 설명: 1..max_dan 단을 결합한 전체 출력 문자열 반환

출력 포맷(정확히):
각 줄: "{dan} x {i} = {dan*i}" (i = 1..9)
단 사이에는 한 줄 공백
최종 문자열의 줄바꿈/공백까지 테스트에서 엄격히 비교

테스트 스펙 (pytest):
- test_generate_dan_lines: generate_dan(1) 및 generate_dan(2)의 첫/마지막 항목 검사
- test_build_full_output_exact: build_full_output(2)의 전체 문자열이 예시와 정확히 일치하는지 검사

CI/실행:
- pytest -q

보안/운영: 이번 PoC는 로컬 실행 전용. 비밀 정보 없음.
