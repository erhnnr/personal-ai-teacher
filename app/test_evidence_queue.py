"""
Knowledge Factory V2 — Phase 5A evidence queue tests.
"""

import json
import sys
from pathlib import Path


TOOLS_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "tools"
)

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS_PATH),
    )

import build_evidence_queue as queue_tool


def record(
    topic,
    exam="AYT",
    subject="Matematik",
):
    return {
        "exam": exam,
        "subject": subject,
        "topic": topic,
        "priority": "HIGH",
    }


def test_missing_evidence_is_queued_for_source_discovery(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        queue_tool,
        "EVIDENCE_ROOT",
        tmp_path,
    )

    item = queue_tool.classify_record(
        record("Olmayan Konu"),
        default_grade="12",
    )

    assert (
        item["evidence_status"]
        == "MISSING"
    )
    assert (
        item["next_action"]
        == "FIND_OFFICIAL_SOURCE"
    )


def test_valid_ready_evidence_is_compile_ready(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        queue_tool,
        "EVIDENCE_ROOT",
        tmp_path,
    )

    path = queue_tool.evidence_path_for(
        "Matematik",
        "12",
        "İntegral",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            {
                "id": "matematik.grade12.integral",
                "exam": "AYT",
                "subject": "Matematik",
                "grade": "12",
                "topic": "İntegral",
                "status": "EVIDENCE_READY",
                "sources": [],
                "claims": [],
                "coverage": {
                    "curriculum_objectives": [],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        queue_tool,
        "validate_evidence_package",
        lambda evidence: True,
    )

    item = queue_tool.classify_record(
        record("İntegral"),
        default_grade="12",
    )

    assert (
        item["evidence_status"]
        == "READY"
    )
    assert (
        item["next_action"]
        == "COMPILE_FACTUAL_DRAFT"
    )


def test_identity_mismatch_is_not_ready(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        queue_tool,
        "EVIDENCE_ROOT",
        tmp_path,
    )

    path = queue_tool.evidence_path_for(
        "Matematik",
        "12",
        "İntegral",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            {
                "id": "wrong",
                "exam": "TYT",
                "subject": "Matematik",
                "grade": "12",
                "topic": "İntegral",
                "status": "EVIDENCE_READY",
                "sources": [],
                "claims": [],
                "coverage": {
                    "curriculum_objectives": [],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        queue_tool,
        "validate_evidence_package",
        lambda evidence: True,
    )

    item = queue_tool.classify_record(
        record("İntegral"),
        default_grade="12",
    )

    assert (
        item["evidence_status"]
        == "DRAFT"
    )
    assert (
        item["next_action"]
        == "FIX_EVIDENCE_IDENTITY"
    )


def test_queue_summary_is_deterministic(
    monkeypatch,
):
    rows = [
        record("A"),
        record("B"),
        record(
            "C",
            exam="TYT",
            subject="Fizik",
        ),
    ]

    states = {
        "A": "READY",
        "B": "MISSING",
        "C": "DRAFT",
    }

    def fake_classify(
        row,
        default_grade="12",
    ):
        status = states[
            row["topic"]
        ]

        return {
            "exam": row["exam"],
            "subject": row["subject"],
            "grade": default_grade,
            "topic": row["topic"],
            "priority": row.get(
                "priority"
            ),
            "evidence_status": status,
            "source_ids": [],
            "evidence_path": "x",
            "next_action": "x",
        }

    monkeypatch.setattr(
        queue_tool,
        "classify_record",
        fake_classify,
    )

    queue = queue_tool.build_queue(
        records=rows,
        default_grade="12",
    )

    assert (
        queue["total_topics"]
        == 3
    )
    assert queue["summary"] == {
        "ready": 1,
        "draft": 1,
        "missing": 1,
    }


def test_source_ids_are_deduplicated():
    evidence = {
        "sources": [
            {
                "source_id": "S1"
            }
        ],
        "claims": [
            {
                "source_refs": [
                    {
                        "source_id": "S1"
                    },
                    {
                        "source_id": "S2"
                    },
                ]
            }
        ],
    }

    assert (
        queue_tool.source_ids_from_evidence(
            evidence
        )
        == [
            "S1",
            "S2",
        ]
    )


def test_display_path_falls_back_outside_project(
    tmp_path,
):
    path = (
        tmp_path
        / "evidence.json"
    )

    assert (
        queue_tool.display_path(
            path
        )
        == str(path)
    )
