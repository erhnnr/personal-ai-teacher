import hashlib
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import compile_ready_evidence_to_canonical as compiler

TEXT = "Resmî kaynak metni."
HASH = hashlib.sha256(TEXT.encode("utf-8")).hexdigest()


def ready_record():
    return {
        "record_id": "R1",
        "outcome_id": "BİY.12.2.1",
        "grade": 12,
        "theme_number": 2,
        "theme_name": "Gen",
        "outcome_title": "Nükleik asitlerin yapısını sorgulayabilme",
        "source": {
            "authority": "MEB",
            "corpus_family": "MEBI_OFFICIAL_LOCAL_CORPUS",
            "package_id": "MEBI-AYT-BIYOLOJI",
            "page": 151,
            "source_anchor": "ayt-biyoloji/index.html#p=151",
            "html_path": "files/basic-html/page151.html",
            "image_path": "files/thumb/151.jpg",
            "text_sha256": HASH,
        },
        "verification": {"status": "VERIFIED_SUPPORT_CANDIDATE"},
        "approval": {
            "status": "APPROVED_FOR_EVIDENCE_READY",
            "reviewer_type": "EXTERNAL_LLM",
            "reviewer_id": "reviewer-1",
            "factual_support": True,
            "outcome_support": True,
            "source_consistency": True,
            "rationale": "checked",
        },
        "promotion_policy": "RELEASE_SAFE_INDEPENDENT_APPROVAL_GATE",
        "evidence_text": TEXT,
        "evidence_status": "READY",
        "student_visible": False,
    }


def test_compiler_copies_evidence_verbatim():
    unit = compiler.compile_record(ready_record())
    assert unit["source_grounded_content"]["text"] == TEXT
    assert unit["source_grounded_content"]["text_sha256"] == HASH


def test_compiler_does_not_invent_structured_facts():
    unit = compiler.compile_record(ready_record())
    assert unit["definitions"] == []
    assert unit["rules"] == []
    assert unit["core_concepts"] == []
    assert unit["common_confusions"] == []


def test_compiled_unit_is_verified_but_not_student_ready():
    unit = compiler.compile_record(ready_record())
    assert unit["verified"] is True
    assert unit["student_ready"] is False
    assert unit["student_visible"] is False


def test_compiled_unit_requires_ready_evidence():
    unit = compiler.compile_record(ready_record())
    unit["verification"]["evidence_status"] = "NOT_READY"
    assert compiler.validate_compiled_unit(unit)


def test_hash_mismatch_is_rejected():
    unit = compiler.compile_record(ready_record())
    unit["source_grounded_content"]["text"] = "tampered"
    assert compiler.validate_compiled_unit(unit)


def test_missing_independent_approval_is_rejected():
    unit = compiler.compile_record(ready_record())
    unit["verification"]["approval_status"] = "REJECTED"
    assert compiler.validate_compiled_unit(unit)


def test_compile_all_writes_concept_and_manifest(tmp_path):
    manifest, errors = compiler.compile_all(
        {"records": [ready_record()]},
        tmp_path / "biology",
    )
    assert errors == []
    assert manifest["compiled_count"] == 1
    assert (tmp_path / "biology" / "biy.12.2.1" / "concept.json").exists()
    assert (tmp_path / "biology" / "manifest.json").exists()


def test_manifest_remains_not_student_ready(tmp_path):
    manifest, errors = compiler.compile_all(
        {"records": [ready_record()]},
        tmp_path / "biology",
    )
    assert errors == []
    assert manifest["student_ready"] is False
    assert manifest["student_visible"] is False


def test_manifest_validation_detects_count_mismatch():
    manifest = {
        "subject": "Biyoloji",
        "input_ready_count": 2,
        "compiled_count": 1,
        "units": [{"id": "A"}],
        "student_ready": False,
        "student_visible": False,
    }
    assert compiler.validate_manifest(manifest)
