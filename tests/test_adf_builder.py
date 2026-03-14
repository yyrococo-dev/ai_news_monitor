import json
from dev_skill.tools.adf_builder import build_doc

def test_build_doc():
    doc = build_doc(['line1','line2'])
    assert isinstance(doc, dict)
    assert doc['type'] == 'doc'
    assert doc['version'] == 1
    assert len(doc['content']) == 2
    assert doc['content'][0]['type'] == 'paragraph'
    assert doc['content'][0]['content'][0]['text'] == 'line1'


def test_build_doc_roundtrip():
    doc = build_doc(['hello'])
    s = json.dumps(doc)
    parsed = json.loads(s)
    assert parsed == doc
