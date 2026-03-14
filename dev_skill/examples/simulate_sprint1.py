#!/usr/bin/env python3
"""Simulate Sprint-1 flow:
1) run_ai_architect -> generates spec.md and sets DESIGN_REVIEW
2) simulate approve-spec comment -> webhook listener logic via direct call
3) run_ai_dev_write -> creates patch
4) run_ai_dev_review -> produces review and posts to Jira
"""
import os, sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]
sys.path.append(str(REPO/'dev_skill'))
from dev_skill.orchestrator import run_ai_architect, run_ai_dev_write, run_ai_dev_review, _get_pipeline_state
from dev_skill.hooks.webhook_listener import _set_pipeline_state

os.environ['JIRA_ISSUE_KEY']='KAN-22'
print('1) run_ai_architect')
run_ai_architect()
print('pipeline_state after architect:', _get_pipeline_state(str(REPO/'storage.db'),'KAN-22'))
print('\n2) simulate approve-spec')
_set_pipeline_state(str(REPO/'storage.db'),'KAN-22','DESIGN_APPROVED',metadata={'approved_by':'SimUser'})
print('pipeline_state after approve:', _get_pipeline_state(str(REPO/'storage.db'),'KAN-22'))
print('\n3) run_ai_dev_write')
run_ai_dev_write()
print('\n4) run_ai_dev_review')
run_ai_dev_review()
print('\nDone simulation')
