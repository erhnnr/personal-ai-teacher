import hashlib
import sys
import unicodedata
from pathlib import Path

APP = Path(__file__).resolve().parent
TOOLS = APP.parent / "tools"

if str(APP) not in sys.path:
    sys.path.insert(
        0,
        str(APP),
    )

if str(TOOLS) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS),
    )

from build_hash_bound_reviewer_packet import (
    find_source_record,
    normalize_record_id,
)
from review_integrity import sha256_text


def record(
    record_id,
    text="Official evidence",
):
    return {
        "record_id": record_id,
        "evidence_text": text,
        "text_sha256": sha256_text(
            text
        ),
    }


def test_source_resolution_finds_fallback_document():
    target = "BİY.10.1.1::MEBI::p10"

    documents = [
        ("summary", {
            "records": [
                {
                    "record_id": target,
                    "status": "READY",
                }
            ]
        }),
        ("review_packet", {
            "records": [
                record(target)
            ]
        }),
    ]

    found = find_source_record(
        target,
        documents,
    )

    assert (
        found["evidence_text"]
        == "Official evidence"
    )


def test_source_resolution_normalizes_unicode_record_id():
    composed = "BİY.10.1.1"
    decomposed = unicodedata.normalize(
        "NFD",
        composed,
    )

    found = find_source_record(
        composed,
        [
            (
                "source",
                {
                    "records": [
                        record(
                            decomposed
                        )
                    ]
                },
            )
        ],
    )

    assert normalize_record_id(
        found["record_id"]
    ) == normalize_record_id(
        composed
    )


def test_conflicting_exact_record_payloads_fail_closed():
    target = "BİY.10.1.1"

    documents = [
        (
            "source-a",
            {
                "records": [
                    record(
                        target,
                        "Text A",
                    )
                ]
            },
        ),
        (
            "source-b",
            {
                "records": [
                    record(
                        target,
                        "Text B",
                    )
                ]
            },
        ),
    ]

    try:
        find_source_record(
            target,
            documents,
        )
    except RuntimeError as exc:
        assert (
            "Conflicting evidence payloads"
            in str(exc)
        )
        return

    raise AssertionError(
        "Conflicting evidence must fail closed."
    )


def test_declared_hash_mismatch_fails_closed():
    target = "BİY.10.1.1"

    bad = record(
        target
    )
    bad[
        "text_sha256"
    ] = "0" * 64

    try:
        find_source_record(
            target,
            [
                (
                    "bad-source",
                    {
                        "records": [
                            bad
                        ]
                    },
                )
            ],
        )
    except RuntimeError as exc:
        assert (
            "Evidence SHA-256 mismatch"
            in str(exc)
        )
        return

    raise AssertionError(
        "Hash mismatch must fail closed."
    )
