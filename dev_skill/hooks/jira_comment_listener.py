#!/usr/bin/env python3
"""
Jira comment polling listener (PoC)
- Polls the given Jira issue for new comments and looks for the exact phrase '진행해줘'.
- When found, writes approval_marker.txt and logs via log_agent_action.

Usage:
  export JIRA_ISSUE_KEY=KAN-19
  python dev_skill/hooks/jira_comment_listener.py

Note: PoC uses polling. In production use webhooks.
"""
import os
import time
from pathlib import Path

sys_path = Path(__file__).resolve().parents[2] / 'dev_skill'
# ensure dev_skill tools importable
import sys
sys.path.append(str(sys_path / 'tools'))

from jira_helper import get_issue_comments  # local helper
from dev_skill.tools.log_agent_action import log_agent_action

ISSUE_KEY = os.environ.get('JIRA_ISSUE_KEY','KAN-19')
POLL_INTERVAL = int(os.environ.get('JIRA_POLL_INTERVAL', '10'))
MARKER = Path(__file__).resolve().parents[1] / 'approval_marker.txt'
seen = set()

print('Starting Jira comment listener for', ISSUE_KEY)
while True:
    try:
        comments = get_issue_comments(ISSUE_KEY)
        for c in comments:
            cid = c.get('id')
            if cid in seen:
                continue
            seen.add(cid)
            body = c.get('body','') or ''
            author = c.get('author', {}).get('displayName')
            print('New comment by', author)
            if '진행해줘' in body:
                MARKER.write_text(f'approved_by: {author}\n')
                log_agent_action('jira-comment-listener','approval_detected',output_hash=author,related_issue=ISSUE_KEY)
                print('Approval detected and logged; exiting')
                raise SystemExit(0)
    except Exception as e:
        print('Error polling Jira:', e)
    time.sleep(POLL_INTERVAL)
