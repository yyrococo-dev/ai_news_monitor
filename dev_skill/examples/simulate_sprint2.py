#!/usr/bin/env python3
"""Simulate Sprint-2 scenarios:
- code-failure -> classifier -> auto-transition to DEVELOPMENT
- design-failure -> classifier -> transition to DESIGN_REVIEW and spec generation
- data-failure -> classifier -> DATA_INVESTIGATION
"""
import os, sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]
sys.path.append(str(REPO/'dev_skill'))
from dev_skill.orchestrator import _set_pipeline_state, _get_pipeline_state
from dev_skill.tools.classify_failure import classify_failure
from dev_skill.tools.log_agent_action import log_agent_action

ISSUE='KAN-22'
DB=str(REPO/'storage.db')

scenarios = {
    'code': 'Traceback (most recent call last):\n  File "app.py", line 10, in <module>\n    raise TypeError("oops")\nTypeError: oops',
    'design': 'API contract mismatch: expected field title but got headline; openapi spec mismatch',
    'data': 'JSONDecodeError: Expecting value: line 1 column 1 (char 0)\nInvalid data received from source: missing timestamp',
}

for k,s in scenarios.items():
    print('--- scenario',k)
    clf = classify_failure(s)
    print('classify ->', clf)
    # simulate writing failure and letting orchestrator logic run: set HUMAN_INTERVENTION and then let classifier auto-transition
    from dev_skill.orchestrator import _set_pipeline_state as set_state
    set_state(DB, ISSUE, 'HUMAN_INTERVENTION', error=s, metadata={'sim':'yes'})
    # simulate orchestrator handling by invoking same logic path: here we just emulate decision
    if clf['label']=='code':
        set_state(DB, ISSUE, 'DEVELOPMENT', metadata={'auto':'code'})
    elif clf['label']=='design':
        set_state(DB, ISSUE, 'DESIGN_REVIEW', metadata={'auto':'design'})
    elif clf['label']=='data':
        set_state(DB, ISSUE, 'DATA_INVESTIGATION', metadata={'auto':'data'})
    print('resulting state:', _get_pipeline_state(DB, ISSUE))

print('done')
