Git Onboarding — ai_news_monitor

목적
- 이 문서는 개발자가 로컬에서 리포지토리 작업(브랜치 → 커밋 → PR)을 안전하게 수행하고, assistant와의 자동화(커밋/푸시/PR 생성)를 신뢰할 수 있도록 설정하는 절차를 담습니다.

환경 요약 (provided)
- 기본 원격 호스트: GitHub
- 기본 브랜치 이름: main
- 인증 방식: SSH keys (권장)
- Git 사용자:
  - name: yyrococo-dev
  - email: (사용자 제공 필요; 아래 예시 참조)

사전 요구사항
1. Git 설치 확인
   - git --version
2. GitHub 계정
   - SSH 키를 GitHub 계정에 등록할 수 있어야 합니다.
3. 터미널(shell)
   - zsh 권장 (macOS 기본)

1) Git 사용자 설정
- 로컬에서 아래 명령을 실행:

  git config --global user.name "yyrococo-dev"
  git config --global user.email "you@example.com"  # 실제 이메일로 교체

2) SSH 키 생성 및 GitHub 등록 (권장)
- 새 SSH 키 생성(없을 경우):

  ssh-keygen -t ed25519 -C "you@example.com"
  # 또는 rsa 필요 시: ssh-keygen -t rsa -b 4096 -C "you@example.com"

- 키 에이전트에 추가:

  eval "$(ssh-agent -s)"
  ssh-add ~/.ssh/id_ed25519

- 공개키 복사 및 GitHub 등록:

  cat ~/.ssh/id_ed25519.pub
  # 복사한 키를 GitHub > Settings > SSH and GPG keys > New SSH key에 붙여넣기

- 연결 테스트:

  ssh -T git@github.com

3) 리포지토리 원격 연결 (예시)
- 기존 로컬 레포가 있다면 origin을 추가:

  git remote add origin git@github.com:YOUR_ORG/ai_news_monitor.git
  git fetch origin
  git branch -M main
  git push -u origin main

- feature 브랜치 푸시 예시:

  git checkout -b feature/my-change
  git add -A
  git commit -m "feat: my change"
  git push -u origin feature/my-change

4) PR 생성(권장: gh CLI 또는 GitHub 웹 UI)
- gh CLI 사용 예:

  gh pr create --base main --head yyrococo-dev:feature/my-change --title "feat: ..." --body "요약 및 테스트"

- PR 템플릿: .github/PULL_REQUEST_TEMPLATE.md를 참고

5) Python 환경 (권장)
- pyenv + pyenv-virtualenv 추천(권장 Python 3.11.x)
- 또는 pyenv가 불가능하면 system python으로 .venv 생성:

  /Users/youruser/.pyenv/versions/3.11.6/bin/python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

6) Assistant 연동 권한 가이드
- Assistant가 가능한 자동 작업:
  - 커밋 생성, 로컬 브랜치 푸시, PR 생성 (사용자 명시적 승인 시)
- Assistant가 수행하려면 사용자는 다음 중 하나 제공:
  - SSH 접근 권한(ssh key 등록 완료) + 원격 URL
  - 또는 HTTPS + GitHub PAT 저장 위치 안내 (대체 방법)
- 외부 영향(실 PR, 배포, 텔레그램 전송 등)은 반드시 Jira에서 '진행해줘' 코멘트 또는 명시적 허가 문구로 승인

추가 정책 (변경됨):
- 신규 레포 생성 기본 정책: private by default (조직 정책에 따라 권한 부여 별도)
- Maker/Checker 규칙: 자동화된 ai-dev가 생성한 PR은 ai-dev-review 또는 사람 리뷰어가 승인할 때까지 병합하지 않습니다. 자동 승인 루프를 피하려면 PR 보호 규칙을 활성화하세요.
- 설계 승인 허들: ai-architect가 생성한 Tech Spec은 반드시 한 명 이상의 인간 테크 리드 승인이 있어야 ai-dev 단계로 진행됩니다.

7) 저장소 권한/토큰(옵션)
- 안전하게 보관: ~/.openclaw/secrets/github.env 파일 또는 OS 키체인 사용 권장
- 예시 파일 형식 (~/.openclaw/secrets/github.env):

  GITHUB_TOKEN=ghp_xxx

8) 예제 명령 모음 (copy-paste)
- 기본 설정:
  git config --global user.name "yyrococo-dev"
  git config --global user.email "you@example.com"

- SSH 키 생성/등록
  ssh-keygen -t ed25519 -C "you@example.com"
  eval "$(ssh-agent -s)"
  ssh-add ~/.ssh/id_ed25519
  cat ~/.ssh/id_ed25519.pub  # GitHub에 등록

- 원격 추가 및 push
  git remote add origin git@github.com:YOUR_ORG/ai_news_monitor.git
  git branch -M main
  git push -u origin main

9) 문제 해결 FAQ
- ssh: Permission denied (publickey)
  - SSH 키가 GitHub에 등록되었는지 확인
  - ssh-agent에 키가 추가되어 있는지 확인
- git push 권한 없음
  - 원격 repo에서 사용자의 권한 확인(쓰기 권한 필요)
- pyenv activate 에러
  - 쉘 init 스크립트(~/.zprofile)에 pyenv init 관련 라인 추가 필요

10) 체크리스트 (완료 기준)
- [ ] git user.name/email 설정
- [ ] SSH 공개키를 GitHub에 등록
- [ ] origin을 추가하고 main 브랜치로 push 성공
- [ ] .venv 생성 및 requirements 설치 성공
- [ ] Assistant 자동작업 동의/승인 방식 이해

마지막으로
- 문서를 repo에 추가해 두었습니다: ONBOARDING_GIT.md
- 원하시면 제가 이 문서를 dev branch에 커밋하고 PR 템플릿과 연결해 두겠습니다.
