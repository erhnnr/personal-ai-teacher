import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_source_backed_evidence_records as builder


def corpus():
    return {
        "packages": [
            {
                "package_id": "MEBI-AYT-BIYOLOJI",
                "pages": [
                    {
                        "page": 170,
                        "text": "DNA replikasyonu genetik bilginin kopyalanmasını sağlar.",
                        "text_status": "READY",
                        "image_status": "LINKED",
                        "source_anchor": "index.html#p=170",
                        "html_path": "files/basic-html/page170.html",
                        "image_path": "files/thumb/170.jpg",
                    }
                ],
            }
        ]
    }


def outcome(status="VERIFIED_SUPPORT_CANDIDATE"):
    return {
        "id": "BİY.12.2.2",
        "grade": 12,
        "theme_number": 2,
        "theme_name": "Gen",
        "title": "DNA replikasyonunun bilimsel modelini oluşturabilme",
        "crosswalk_status": "STRONG_CANDIDATE",
        "verification_status": status,
        "best_candidate": {
            "package_id": "MEBI-AYT-BIYOLOJI",
            "page": 170,
            "crosswalk_score": 123.0,
            "crosswalk_status": "STRONG_CANDIDATE",
            "matched_title_tokens": ["dna", "replikasyonunun", "modelini"],
            "matched_title_bigrams": ["dna replikasyonunun"],
            "checks": {
                "candidate_page_exists": True,
                "official_biology_package": True,
                "text_ready": True,
                "source_anchor_present": True,
                "html_path_present": True,
                "image_path_present": True,
                "package_affinity": True,
                "distinctive_title_hit_count": 3,
                "title_bigram_hit_count": 1,
            },
        },
    }


def test_verified_outcome_builds_record():
    lookup = builder.build_page_lookup(corpus())
    record = builder.build_record(
        outcome(),
        lookup,
    )
    assert record["outcome_id"] == "BİY.12.2.2"
    assert record["review_status"] == "REVIEW_PENDING"
    assert record["evidence_status"] == "NOT_READY"
    assert record["student_visible"] is False


def test_record_preserves_verbatim_page_text():
    lookup = builder.build_page_lookup(corpus())
    record = builder.build_record(
        outcome(),
        lookup,
    )
    assert (
        record["evidence_text"]
        == "DNA replikasyonu genetik bilginin kopyalanmasını sağlar."
    )


def test_record_contains_complete_provenance():
    lookup = builder.build_page_lookup(corpus())
    record = builder.build_record(
        outcome(),
        lookup,
    )
    source = record["source"]
    assert source["authority"] == "MEB"
    assert source["package_id"] == "MEBI-AYT-BIYOLOJI"
    assert source["page"] == 170
    assert source["source_anchor"]
    assert source["html_path"]
    assert source["image_path"]
    assert len(source["text_sha256"]) == 64


def test_non_verified_outcome_is_not_emitted():
    verification = {
        "outcomes": [
            outcome("REVIEW_REQUIRED")
        ]
    }
    payload = builder.build_records(
        verification,
        corpus(),
    )
    assert payload["record_count"] == 0


def test_missing_provenance_rejected():
    bad = corpus()
    bad["packages"][0]["pages"][0]["source_anchor"] = None

    lookup = builder.build_page_lookup(bad)

    try:
        builder.build_record(
            outcome(),
            lookup,
        )
    except ValueError as exc:
        assert "source_anchor" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_payload_validation_protects_release_state():
    verification = {
        "outcomes": [
            outcome()
        ]
    }
    payload = builder.build_records(
        verification,
        corpus(),
    )

    payload["records"][0]["evidence_status"] = "READY"

    errors = builder.validate_payload(
        payload
    )

    assert any(
        "NOT_READY" in error
        for error in errors
    )


def test_text_hash_is_deterministic():
    a = builder.text_sha256("abc")
    b = builder.text_sha256("abc")
    assert a == b
    assert len(a) == 64
