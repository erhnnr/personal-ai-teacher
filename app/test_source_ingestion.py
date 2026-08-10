"""
Tests for Knowledge Factory V2 source ingestion.
"""

import json
import sys
from pathlib import Path

import pytest


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

import source_ingestion


def test_normalize_values():
    assert source_ingestion.normalize_values(
        [
            "Matematik",
            " Matematik ",
            "",
            "Fizik",
        ]
    ) == [
        "Matematik",
        "Fizik",
    ]


def test_build_url_source_record():
    record = (
        source_ingestion
        .build_source_record(
            source_id="OGM-MAT12-LIMIT",
            publisher="MEB OGM",
            title=(
                "12. Sınıf Matematik "
                "Beceri Temelli Etkinlik Kitabı"
            ),
            source_type="activity_book",
            authority_tier=(
                "primary_official"
            ),
            url=(
                "https://example.test/"
                "official"
            ),
            exam_scope=["AYT"],
            subject_scope=["Matematik"],
            grade_scope=["12"],
            topic_scope=["Limit"],
        )
    )

    assert (
        record["id"]
        == "OGM-MAT12-LIMIT"
    )

    assert (
        record["topic_scope"]
        == ["Limit"]
    )


def test_local_source_gets_hash(
    tmp_path,
    monkeypatch,
):
    local_file = (
        tmp_path
        / "source.txt"
    )

    local_file.write_text(
        "resmi kaynak",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        source_ingestion,
        "PROJECT_ROOT",
        tmp_path,
    )

    record = (
        source_ingestion
        .build_source_record(
            source_id="LOCAL-1",
            publisher="MEB",
            title="Local official source",
            source_type="curriculum",
            authority_tier=(
                "primary_official"
            ),
            local_path="source.txt",
            exam_scope=["TYT"],
            subject_scope=["Matematik"],
            grade_scope=["12"],
            topic_scope=["Limit"],
        )
    )

    assert len(
        record["sha256"]
    ) == 64

    assert (
        record["local_path"]
        == "source.txt"
    )


def test_register_rejects_duplicate(
    tmp_path,
    monkeypatch,
):
    schema = {
        "$schema": (
            "https://json-schema.org/"
            "draft/2020-12/schema"
        ),
        "type": "object",
        "required": [
            "id",
            "publisher",
            "title",
            "source_type",
            "authority_tier",
            "exam_scope",
            "subject_scope",
            "grade_scope",
            "topic_scope",
        ],
        "properties": {
            "id": {"type": "string"},
            "publisher": {
                "type": "string"
            },
            "title": {
                "type": "string"
            },
            "source_type": {
                "type": "string"
            },
            "authority_tier": {
                "type": "string"
            },
            "url": {
                "type": "string"
            },
            "exam_scope": {
                "type": "array"
            },
            "subject_scope": {
                "type": "array"
            },
            "grade_scope": {
                "type": "array"
            },
            "topic_scope": {
                "type": "array"
            },
            "notes": {
                "type": "array"
            },
        },
    }

    schema_path = (
        tmp_path
        / "source_record.schema.json"
    )

    schema_path.write_text(
        json.dumps(schema),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        source_ingestion,
        "SOURCE_SCHEMA_PATH",
        schema_path,
    )

    registry_path = (
        tmp_path
        / "source_registry.json"
    )

    registry_path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "id": "SRC-1"
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    record = {
        "id": "SRC-1",
        "publisher": "MEB",
        "title": "Official source",
        "source_type": "curriculum",
        "authority_tier": (
            "primary_official"
        ),
        "url": (
            "https://example.test/source"
        ),
        "exam_scope": ["AYT"],
        "subject_scope": ["Matematik"],
        "grade_scope": ["12"],
        "topic_scope": ["Limit"],
        "notes": [],
    }

    with pytest.raises(
        ValueError,
        match="Duplicate source id",
    ):
        source_ingestion.register_source(
            record,
            registry_path=registry_path,
        )
