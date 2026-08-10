"""
Knowledge Factory V2 Phase 3.4 structured-output contract tests.
"""

import sys
from pathlib import Path

TOOLS_PATH = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))

import generate_knowledge_batch as generator


def test_response_format_is_json_schema():
    response_format = generator.build_structured_response_format()
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    schema = response_format["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert "concept" in schema["properties"]


def test_optional_evidence_limited_arrays_may_be_empty():
    schema = generator.build_structured_response_format()["json_schema"]["schema"]
    concept = schema["properties"]["concept"]["properties"]
    assert "minItems" not in concept["definitions"]
    assert "minItems" not in concept["rules"]
    examples = schema["properties"]["examples"]["properties"]["examples"]
    assert "minItems" not in examples
