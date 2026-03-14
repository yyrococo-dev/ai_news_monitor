#!/usr/bin/env python3
from flask import Flask, request, jsonify
from pathlib import Path
import os
import hmac
import hashlib
import subprocess
import sys
import json

# Webhook listener for Jira comment events.
# - '진행해줘' -> marks approval (existing behavior)
# - '재실행해줘' -> clear HUMAN_INTERVENTION for issue and trigger orchestrator restart
# Security: in production, verify payload signatures, restrict IPs, and run behind TLS.

APP = Flask(__name__)
SECRET = os.environ.get('WEBHOOK_SECRET','dev-skill-secret')
MARKER = Path(__file__).resolve().parents[1] / 'approval_marker.txt'
REPO_ROOT = Path(__file__).resolve().parents[2]
STORAGE_DB = str(REPO_ROOT/'storage.db')
ORCHESTRATOR = REPO_ROOT / 'dev_skill' / 'orchestrator.py'


def verify_signature(raw_body, signature_header):
    # PoC: use HMAC-SHA256 with SECRET
    if not signature_header:
        return False
    try:
        received = signature_header.split('=')[1]
    except Exception:
        return False
    mac = hmac.new(SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, received)


def _set_pipeline_state(db_path: str, issue_key: str, state: str, error: str = None, metadata: dict = None):
    import sqlite3, datetime
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        ts = datetime.datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata or {})
        cur.execute('INSERT INTO pipeline_state (issue_key,state,failure_count,last_error,last_ts,metadata) VALUES (?,?,?,?,?,?) ON CONFLICT(issue_key) DO UPDATE SET state=excluded.state, last_error=excluded.last_error, last_ts=excluded.last_ts, metadata=excluded.metadata', (issue_key, state, 0, error, ts, meta_json))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print('Failed to set pipeline_state', e, file=sys.stderr)
        return False


@APP.route('/webhook', methods=['POST'])
def webhook():
    sig = request.headers.get('X-Hub-Signature-256')
    raw = request.get_data()
    if not verify_signature(raw, sig):
        return jsonify({'error':'invalid signature'}), 403
    data = request.json or {}
    # PoC: Jira webhook payload varies; look for comment body
    comment = None
    issue_key = data.get('issue',{}).get('key') or data.get('issue',{}).get('id')
    author = None
    # Try common Jira webhook shapes
    if 'comment' in data and isinstance(data['comment'], dict):
        comment = data['comment'].get('body')
        author = data['comment'].get('author',{}).get('displayName')
    else:
        # fallback: search for nested comment
        for k,v in data.items():
            if isinstance(v, dict) and 'comment' in v:
                comment = v['comment'].get('body')
                author = v['comment'].get('author',{}).get('displayName')
    if not comment:
        return jsonify({'status':'ignored','reason':'no_comment'}), 200

    text = comment.lower()
    # approval
    if '진행해줘' in text:
        MARKER.write_text(f'approved_by: {author}\n')
        try:
            from dev_skill.tools.log_agent_action import log_agent_action
            log_agent_action('webhook-listener','approval_detected',output_hash=author,related_issue=issue_key)
        except Exception:
            pass
        return jsonify({'status':'approved'}), 200

    # design approval/rejection handling
    if 'approve-spec' in text:
        if not issue_key:
            return jsonify({'error':'no_issue_key'}), 400
        ok = _set_pipeline_state(STORAGE_DB, issue_key, 'DESIGN_APPROVED', metadata={'approved_by': author})
        try:
            from dev_skill.tools.log_agent_action import log_agent_action
            log_agent_action('webhook-listener','spec_approved',output_hash=author,related_issue=issue_key, db_path=STORAGE_DB)
        except Exception:
            pass
        return jsonify({'status':'spec_approved'}), 200
    if 'reject-spec' in text or 'revise-spec' in text:
        if not issue_key:
            return jsonify({'error':'no_issue_key'}), 400
        ok = _set_pipeline_state(STORAGE_DB, issue_key, 'DESIGN_REVIEW', metadata={'rejected_by': author})
        try:
            from dev_skill.tools.log_agent_action import log_agent_action
            log_agent_action('webhook-listener','spec_rejected',output_hash=author,related_issue=issue_key, db_path=STORAGE_DB)
        except Exception:
            pass
        return jsonify({'status':'spec_rejected'}), 200

    # resume command: clear HUMAN_INTERVENTION and restart orchestrator for that issue
    if '재실행해줘' in text or 'resume' in text:
        if not issue_key:
            return jsonify({'error':'no_issue_key'}), 400
        # set pipeline state to IN_PROGRESS
        ok = _set_pipeline_state(STORAGE_DB, issue_key, 'IN_PROGRESS', metadata={'resumed_by': author})
        try:
            from dev_skill.tools.log_agent_action import log_agent_action
            log_agent_action('webhook-listener','resume_requested',output_hash=author,related_issue=issue_key, db_path=STORAGE_DB)
        except Exception:
            pass
        if not ok:
            return jsonify({'status':'failed','reason':'db_update'}), 500
        # spawn orchestrator as a separate process to handle the issue (detached)
        try:
            env = os.environ.copy()
            env['JIRA_ISSUE_KEY'] = issue_key
            # run in background; use nohup style subprocess
            subprocess.Popen([sys.executable, str(ORCHESTRATOR)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return jsonify({'status':'restarted'}), 200
        except Exception as e:
            print('Failed to spawn orchestrator', e, file=sys.stderr)
            return jsonify({'status':'failed','reason':'spawn','error':str(e)}), 500

    return jsonify({'status':'ignored'}), 200


if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=int(os.environ.get('WEBHOOK_PORT','8080')))
