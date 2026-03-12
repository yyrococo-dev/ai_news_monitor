# Jira comment templates for Orchestrator
from datetime import datetime

def detailed_stage_template(stage, status, summary, audit_id=None, artifacts=None, next_steps=None):
    ts = datetime.utcnow().isoformat() + 'Z'
    artifacts = artifacts or []
    parts = []
    parts.append(f"(SUJI) 파이프라인 상태 보고")
    parts.append(f"- 단계: {stage}")
    parts.append(f"- 상태: {status}")
    if summary:
        parts.append(f"- 요약: {summary}")
    if audit_id:
        parts.append(f"- agent_audit id: {audit_id}")
    if artifacts:
        parts.append(f"- 주요 아티팩트:")
        for i,(label,path) in enumerate(artifacts, start=1):
            parts.append(f"  {i}. {label}: {path}")
    if next_steps:
        parts.append(f"- 권장 후속: {next_steps}")
    parts.append(f"- 보고시간: {ts}")
    return "\n".join(parts)
