#!/usr/bin/env python3
"""
Simple Jira approval listener PoC.
- Polls a Jira issue's comments and looks for the exact text '진행해줘'.
- When found, records an audit log entry and writes an approval marker file.

Note: This is a polling PoC. In production use webhooks.
"""
import time
from pathlib import Path
import os
import sys
sys.path.append(str(Path.home()/'.openclaw'/'tools'))
from jira_helper import get_issue_comments
from dev_skill.tools.log_agent_action import log_agent_action

ISSUE_KEY = os.environ.get('JIRA_ISSUE_KEY','KAN-15')
POLL_INTERVAL = 10
MARKER = Path(__file__).resolve().parents[2] / 'dev_skill' / 'hooks' / 'approval_marker.txt'

seen_comment_ids = set()


def check_comments():
    comments = get_issue_comments(ISSUE_KEY)
    for c in comments:
        cid = c.get('id')
        if cid in seen_comment_ids:
            continue
        seen_comment_ids.add(cid)
        body = c.get('body','')
        author = c.get('author', {}).get('displayName')
        if '진행해줘' in body:
            print('Approval comment found by', author)
            MARKER.write_text(f'approved_by: {author}\n')
            log_agent_action('ai-approval-listener','approval_detected', related_issue=ISSUE_KEY, output_hash=author)
            return True
    return False


if __name__ == '__main__':
    print('Starting Jira approval listener PoC for', ISSUE_KEY)
    while True:
        try:
            if check_comments():
                print('Approval detected; exiting listener')
                break
        except Exception as e:
            print('Error checking comments:', e)
        time.sleep(POLL_INTERVAL)
