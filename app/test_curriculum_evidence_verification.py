import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import verify_curriculum_evidence as verifier


def make_corpus(text="DNA replikasyonu genetik bilginin kopyalanması"):
    return {
        "packages": [
            {
                "package_id": "MEBI-AYT-BIYOLOJI",
                "pages": [
                    {
                        "page": 170,
                        "text": text,
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


def make_outcome(title="DNA replikasyonu ve genetik bilginin kopyalanması"):
    return {
        "id": "BİY.12.2.2",
        "grade": 12,
        "theme_number": 2,
        "theme_name": "Gen",
        "title": title,
        "mapping_status": "STRONG_CANDIDATE",
        "candidate_pages": [
            {
                "package_id": "MEBI-AYT-BIYOLOJI",
                "page": 170,
                "score": 100.0,
            }
        ],
    }


def test_normalization_handles_turkish_i():
    assert verifier.normalize_text("BİYOLOJİ") == "biyoloji"


def test_complete_specific_candidate_is_verified_support_candidate():
    lookup = verifier.build_page_lookup(make_corpus())
    result = verifier.verify_candidate(
        make_outcome(),
        make_outcome()["candidate_pages"][0],
        lookup,
    )
    assert (
        result["verification_status"]
        == "VERIFIED_SUPPORT_CANDIDATE"
    )


def test_single_distinctive_hit_requires_review():
    lookup = verifier.build_page_lookup(
        make_corpus("DNA başka içerik")
    )
    result = verifier.verify_candidate(
        make_outcome("DNA replikasyonu"),
        make_outcome("DNA replikasyonu")["candidate_pages"][0],
        lookup,
    )
    assert result["verification_status"] == "REVIEW_REQUIRED"


def test_missing_page_is_rejected():
    lookup = verifier.build_page_lookup(make_corpus())
    bad_candidate = {
        "package_id": "MEBI-AYT-BIYOLOJI",
        "page": 999,
        "score": 1.0,
    }
    result = verifier.verify_candidate(
        make_outcome(),
        bad_candidate,
        lookup,
    )
    assert result["verification_status"] == "REJECTED"


def test_evidence_status_never_becomes_ready():
    crosswalk = {
        "outcomes": [
            make_outcome()
        ]
    }
    payload = verifier.build_verification(
        crosswalk,
        make_corpus(),
    )
    assert payload["outcomes"][0]["evidence_status"] == "NOT_READY"


def test_missing_provenance_cannot_be_verified():
    corpus = make_corpus()
    corpus["packages"][0]["pages"][0]["source_anchor"] = None
    lookup = verifier.build_page_lookup(corpus)

    result = verifier.verify_candidate(
        make_outcome(),
        make_outcome()["candidate_pages"][0],
        lookup,
    )
    assert result["verification_status"] == "REJECTED"


def test_validation_rejects_wrong_canonical_count():
    payload = {
        "subject": "Biyoloji",
        "curriculum_outcome_count": 1,
        "outcomes": [],
    }
    errors = verifier.validate_verification(payload)
    assert any("78" in error for error in errors)
