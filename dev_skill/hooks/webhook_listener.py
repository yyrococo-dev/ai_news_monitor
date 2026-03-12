#!/usr/bin/env python3
from flask import Flask, request, jsonify
from pathlib import Path
import os
import hmac
import hashlib

# Simple webhook listener PoC for Jira approval webhooks.
# Security: in production, verify payload signatures and use HTTPS.

APP = Flask(__name__)
SECRET = os.environ.get('WEBHOOK_SECRET','dev-skill-secret')
MARKER = Path(__file__).resolve().parents[1] / 'approval_marker.txt'


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


@APP.route('/webhook', methods=['POST'])
def webhook():
    sig = request.headers.get('X-Hub-Signature-256')
    raw = request.get_data()
    if not verify_signature(raw, sig):
        return jsonify({'error':'invalid signature'}), 403
    data = request.json or {}
    # PoC: Jira webhook payload varies; look for comment body
    comment = None
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
    if comment and '진행해줘' in comment:
        MARKER.write_text(f'approved_by: {author}\n')
        # append audit log via existing helper if available
        try:
            from dev_skill.tools.log_agent_action import log_agent_action
            log_agent_action('webhook-listener','approval_detected',output_hash=author,related_issue=data.get('issue',{}).get('key'))
        except Exception:
            pass
        return jsonify({'status':'approved'}), 200
    return jsonify({'status':'ignored'}), 200


if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=8080)
