WBS: Orchestrator & Pipeline Improvements

Overview

Goal: Harden the Orchestrator pipeline with clear roles (ai-architect), Maker/Checker separation, robust failure handling (max_retries → HUMAN_INTERVENTION), audit linkage, and report artifacts. Deliver incremental work in Sprint-0 → Sprint-2.

Sprint-0 (Immediate: DB + retry + notifier)
- 0.1 Add pipeline_state table to storage.db
  - fields: issue_key (PK), state, failure_count, last_error, last_ts, metadata(JSON)
- 0.2 Implement MAX_RETRIES and RETRY_BACKOFF config (env vars ORCH_MAX_RETRIES, ORCH_RETRY_BACKOFF)
- 0.3 Ensure log_agent_action supports db_path and returns inserted id (done)
- 0.4 Make Orchestrator write/consult pipeline_state and increment failure_count on step failures
- 0.5 HUMAN_INTERVENTION state: trigger ai-notifier to send alert (Telegram/Slack) with links and agent_audit ids
- 0.6 Record Jira comment_id in agent_audit when posting comments (done)
- 0.7 Add tests: simulate failing step → verify failure_count increment and HUMAN_INTERVENTION after MAX_RETRIES

Sprint-1 (Design gating + Maker/Checker)
- 1.1 Add ai-architect stage before ai-dev
  - run_ai_architect: generate Tech Spec (spec.md), OpenAPI stub, ERD sketch, save to repo/reports/<ISSUE>/spec.md
  - Create human-approval gate: require explicit Jira approval comment ("approve-spec") to allow ai-dev to proceed
- 1.2 Split ai-dev into ai-dev-write and ai-dev-review substeps
  - ai-dev-write: create branch + PR + unit-test changes
  - ai-dev-review: run static analysis (ruff/flake/mypy) and generate review comments; do NOT auto-approve PR
- 1.3 Protect main branch: require CI + human review before merge
- 1.4 Add pipeline_state transitions for design-review cycles

Sprint-2 (Classification, reports, UX)
- 2.1 Implement classify_failure(logs) to route QA failures: code vs design vs data
- 2.2 Auto-rollback transitions: QA failure -> DEVELOPMENT or DESIGN based on classification
- 2.3 Publish reports to repo/reports/<ISSUE>/ and optionally to external hosting (S3/Gist)
- 2.4 Add dashboard or Slack actionable messages for HUMAN_INTERVENTION events
- 2.5 Add unit/integration tests and documentation updates (ONBOARDING_GIT.md, SKILL.md)

Owners & Acceptance
- Owner: dev_skill maintainers (initially: 미니 / 수지 agent)
- Acceptance: Automated test demonstrating state transitions + manual verify of KAN-22 simulated flow with HUMAN_INTERVENTION path

Notes
- Default policy: plain-text Jira comments; ADF as opt-in. External-effect actions (push/merge/deploy) always require explicit human approval.

