DRAFT — ONBOARDING updates (for review)

STATUS: DRAFT — do not publish. This file is a working draft that collects Sprint-0 changes and will be merged into ONBOARDING.md after review and sign-off.

Key additions (Sprint-0)

1) Pipeline state & retries
- Orchestrator now maintains a pipeline_state table in storage.db with fields: issue_key, state, failure_count, last_error, last_ts, metadata.
- Environment variables:
  - ORCH_MAX_RETRIES (default 3)
  - ORCH_RETRY_BACKOFF (seconds, optional)
- Behavior: when a pipeline step fails, failure_count increments. If failure_count >= ORCH_MAX_RETRIES, pipeline transitions to HUMAN_INTERVENTION and an automatic Jira comment is posted requesting human action. Agent_audit entries record these events.

2) Plain-text Jira comments + audit linkage
- By default Orchestrator posts plain-text comments to Jira; ADF posts are optional.
- Each posted comment's comment_id is recorded in agent_audit for traceability.

3) Reports
- Orchestrator stores run artifacts and a short report under repo/reports/<ISSUE>/ (e.g., REPORT_KAN-22.md, orch.log). These are committed to the feature branch for inspection.

4) Safety & approvals
- External-effect actions (push/merge/deploy) remain blocked until explicit human approval (Jira comment '진행해줘' or equivalent).

Human intervention
- When pipeline_state transitions to HUMAN_INTERVENTION the Orchestrator will stop further automated progress for that issue and post a clear Jira comment requesting manual action. A human must resolve the underlying cause and post an explicit Jira comment (e.g., 'resume' or '진행해줘') before the Orchestrator will resume.

Suggested next steps before finalizing ONBOARDING.md
- Review wording and acceptance criteria.
- Decide on human approver roles (who can approve specs and merges).
- Add sample Jira comments and a short tutorial 'How to approve' for reviewers.

