#!/usr/bin/env python3
"""
Orchestrator (dry-run) for AI-agent pipeline:
- Runs ai-dev example, then ai-integrator, then ai-qa in sequence.
- Each step logs via log_agent_action and respects dev-skill RULES (dry-run by default).
- Intended for local/simulated runs; can be wired into sessions_spawn or cron later.
"""
import subprocess
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'tools'))
from log_agent_action import log_agent_action

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / 'examples'


def run_ai_dev():
    # run the example script logic directly
    print('Running ai-dev example...')
    dev_script = EXAMPLES_DIR / 'ai_dev_example.py'
    subprocess.check_call([sys.executable, str(dev_script)])
    log_agent_action('orchestrator','ran_ai_dev')


def run_ai_integrator():
    print('Running ai-integrator example...')
    integrator_script = EXAMPLES_DIR / 'ai_integrator_example.sh'
    subprocess.check_call(['bash', str(integrator_script)])
    log_agent_action('orchestrator','ran_ai_integrator')


def run_ai_qa():
    print('Running ai-qa simulation (dry-run)')
    # placeholder - real QA runner would invoke pytest or QA jobs
    log_agent_action('orchestrator','ran_ai_qa')


if __name__ == '__main__':
    print('Orchestrator (dry-run) start')
    run_ai_dev()
    run_ai_integrator()
    run_ai_qa()
    print('Orchestrator finished')
