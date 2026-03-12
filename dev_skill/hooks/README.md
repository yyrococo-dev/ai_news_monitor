Webhook listener PoC (dev_skill)

Purpose
- Lightweight Flask app to receive Jira webhook events (comments). When a comment containing the exact phrase "진행해줘" is posted, the listener writes an approval marker and logs an audit entry.

Security (PoC)
- The PoC expects a HMAC-SHA256 signature in header X-Hub-Signature-256 using environment variable WEBHOOK_SECRET.
- In production, run behind HTTPS and verify requests using secrets/certificates, limit IPs, and use auth tokens.

Run locally (dev)
1) Install deps (recommended into a venv):
   python3 -m venv .venv
   . .venv/bin/activate
   pip install flask requests

2) Start the listener:
   export WEBHOOK_SECRET=your-secret
   python dev_skill/hooks/webhook_listener.py

Expose to internet for Jira webhooks (ngrok example)
1) Start ngrok on port 8080:
   ngrok http 8080
2) Copy public URL (e.g. https://abc123.ngrok.io) and configure Jira webhook:
   - URL: https://abc123.ngrok.io/webhook
   - Events: Issue commented (or comment created)
   - Add a secret header or HMAC secret as configured

Testing
- After wiring webhook in Jira (or using curl to POST), post a comment with body containing "진행해줘" on the target issue (KAN-15).
- The listener will create dev_skill/hooks/approval_marker.txt and log an audit entry (if log_agent_action available).

Notes
- This is a PoC for developer/testing. For production, implement proper authentication, HTTPS, logging, and error handling.
