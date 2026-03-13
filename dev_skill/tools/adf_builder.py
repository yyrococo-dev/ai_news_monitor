"""Simple ADF builder utilities.
Provides helpers to build basic ADF document structures for Jira comments.
"""
from typing import List, Dict


def paragraph(text: str) -> Dict:
    return {'type': 'paragraph', 'content': [{'type': 'text', 'text': text}]}


def build_doc(paragraphs: List[str]) -> Dict:
    return {'type': 'doc', 'version': 1, 'content': [paragraph(p) for p in paragraphs]}


if __name__ == '__main__':
    import json
    print(json.dumps(build_doc(['hello world','second line']), indent=2))
