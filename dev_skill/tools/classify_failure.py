"""
Simple rule-based failure classifier.
Outputs: { 'label': 'code'|'design'|'data'|'other', 'score': float, 'reason': str }

Heuristics: keyword matching with weighted scores.
"""
from typing import Dict

KEYWORDS = {
    'code': ['traceback', 'exception', 'syntaxerror', 'typeerror', 'nullpointer', 'segmentation', 'assertionerror', 'stacktrace'],
    'design': ['api mismatch', 'openapi', 'schema mismatch', 'contract', 'spec', 'design', 'errod', 'erd'],
    'data': ['parse error', 'invalid data', 'missing field', 'csv', 'json decode', 'timestamp', 'corrupt', 'encoding']
}

def classify_failure(log_text: str) -> Dict:
    text = (log_text or '').lower()
    scores = {k:0 for k in KEYWORDS}
    for label, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[label] += 1
    # pick best
    best = max(scores.items(), key=lambda x: x[1])
    label, count = best
    total = sum(scores.values())
    score = (count / total) if total>0 else 0.0
    if total == 0:
        label = 'other'
        score = 0.0
    reason = f"matched {count} keywords for {label}"
    return {'label': label, 'score': float(score), 'reason': reason}

if __name__=='__main__':
    import sys
    s = sys.stdin.read()
    print(classify_failure(s))
