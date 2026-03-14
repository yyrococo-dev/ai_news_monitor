---
name: dev_skill
description: OpenClaw skill for dev_skill orchestration, webhook PoC, and developer utilities (ADF builder, failure classifier). Use when automating pipeline tasks: generate spec, run simulated dev pipeline, build simple ADF comments, or audit agent actions. NOT for running production webhooks without hardening (WSGI/TLS/IP allowlist/author verification required).
---

# dev_skill (초안)

이 스킬은 개발용으로 dev_skill 오케스트레이터와 관련 유틸리티를 패키징한 초안입니다. 주 목적은 내부 개발/테스트 재현성 제공이며, 운영 배포 전 반드시 하드닝(운영용 WSGI, TLS, IP 허용목록, 키 관리, 작성자 검증)을 수행해야 합니다.

주요 포함 항목(초안):
- scripts/: 개발·테스트에 유용한 스크립트 모음 (오케스트레이터, 예제, ADF 빌더)
- references/: ai-architect 산출물(예: reports/KAN-25/spec.md) 및 온보딩 초안

보안 주의사항 (반드시 읽을 것):
- 비밀(토큰, API 키, ngrok authtoken 등)은 절대 스킬에 포함하지 마십시오. 운영 시에는 Secret Manager/GitHub Secrets/OS keychain을 사용하세요.
- webhook_listener는 PoC 코드입니다. 운영에 배포하기 전에 WSGI(gunicorn)로 전환하고 TLS, IP allowlist, 작성자 권한 검증을 추가하세요.

간단한 사용 예:
- 스킬 레퍼런스의 reports/KAN-25/spec.md를 참조하여 로컬에서 Orchestrator 시뮬레이션을 실행할 수 있습니다.

참고: 이 버전은 초안이며, 이후 패키지 정리(파일 이동/경량화) 및 검증을 거쳐 OpenClaw 정식 스킬로 패키징됩니다.
