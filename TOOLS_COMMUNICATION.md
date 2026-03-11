# Communication rules (auto-applied suggestions)

Summary:
- Use WBS or Jira for all tasks. Include WBS or Jira key in commit/PR messages.
- Minimal automated alerts; require manual approval for infra changes.

Quick templates

- Commit message: [WBS-<id>] <type>: short summary
- PR template: See .github/PULL_REQUEST_TEMPLATE.md

Approval rules
- Infra or system changes (pmset, launchd, webhook setup) require explicit approval from TW before applying.

Automation
- Assistant may perform routine repo hygiene changes (gitignore, requirements, small scaffolding) without prior approval but will always record changes in WBS and commit with message referencing WBS.
- Anything that impacts external services or system settings will be proposed and only applied after user confirmation.
