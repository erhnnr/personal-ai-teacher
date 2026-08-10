import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_student_release_manifest as builder


def canonical_manifest():
    return {
        "units": [
            {
                "id": "BİY.10.2.7",
                "record_id": "R1",
                "path": "data/knowledge/canonical_ready/biology/biy.10.2.7/concept.json",
                "text_sha256": "a" * 64,
                "verified": True,
                "student_ready": False,
                "student_visible": False,
            }
        ]
    }


def test_release_manifest_releases_verified_immutable_unit():
    payload = builder.build_release_manifest(canonical_manifest())
    assert payload["release_count"] == 1
    item = payload["units"][0]
    assert item["status"] == "RELEASED"
    assert item["student_ready"] is True
    assert item["student_visible"] is True


def test_release_manifest_does_not_release_mutated_canonical_visibility():
    data = canonical_manifest()
    data["units"][0]["student_visible"] = True
    payload = builder.build_release_manifest(data)
    assert payload["release_count"] == 0


def test_release_manifest_validation():
    payload = builder.build_release_manifest(canonical_manifest())
    assert builder.validate_release_manifest(payload) == []
