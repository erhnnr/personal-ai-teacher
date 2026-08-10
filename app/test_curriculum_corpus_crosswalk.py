import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_curriculum_corpus_crosswalk as crosswalk


def synthetic_registry():
    return {
        "grade_records": [
            {
                "grade": 12,
                "themes": [
                    {
                        "theme_number": 2,
                        "theme_name": "Gen",
                        "content_framework": (
                            "Nükleik Asitler ve Gen İfadesi "
                            "DNA ve RNA'nın Moleküler Yapısı "
                            "DNA Replikasyonu Transkripsiyon Translasyon"
                        ),
                        "learning_outcomes": [
                            {
                                "id": "BİY.12.2.1",
                                "title": (
                                    "Nükleik asitlerin yapısını ve "
                                    "canlılıktaki rolünü sorgulayabilme"
                                ),
                                "source_page": 79,
                            }
                        ],
                    }
                ],
            }
        ]
    }


def synthetic_corpus():
    return {
        "packages": [
            {
                "package_id": "MEBI-TYT-MATEMATIK",
                "pages": [
                    {
                        "page": 1,
                        "text": "Fonksiyonlar polinomlar denklemler",
                    }
                ],
            },
            {
                "package_id": "MEBI-AYT-BIYOLOJI",
                "pages": [
                    {
                        "page": 10,
                        "text": (
                            "Nükleik asitler DNA ve RNA'nın moleküler "
                            "yapısı canlılıktaki rolü"
                        ),
                        "source_anchor": "index.html#p=10",
                    },
                    {
                        "page": 11,
                        "text": "Ekoloji popülasyon komünite ekosistem",
                    },
                ],
            },
        ]
    }


def test_only_biology_packages_are_indexed():
    pages = list(
        crosswalk.iter_biology_pages(
            synthetic_corpus()
        )
    )
    assert len(pages) == 2
    assert {
        page["package_id"]
        for page in pages
    } == {
        "MEBI-AYT-BIYOLOJI"
    }


def test_outcome_count_from_registry_structure():
    outcomes = list(
        crosswalk.iter_curriculum_outcomes(
            synthetic_registry()
        )
    )
    assert len(outcomes) == 1
    assert outcomes[0]["id"] == "BİY.12.2.1"
    assert outcomes[0]["theme_name"] == "Gen"


def test_matching_page_ranks_first():
    pages = list(
        crosswalk.iter_biology_pages(
            synthetic_corpus()
        )
    )
    page_index, df = crosswalk.build_page_index(
        pages
    )
    outcome = next(
        crosswalk.iter_curriculum_outcomes(
            synthetic_registry()
        )
    )
    candidates = crosswalk.rank_candidates(
        outcome,
        page_index,
        df,
        top_k=2,
    )
    assert candidates[0]["page"] == 10
    assert "nükleik" in candidates[0]["title_hits"]


def test_crosswalk_never_marks_evidence_ready():
    payload = crosswalk.build_crosswalk(
        synthetic_registry(),
        synthetic_corpus(),
        top_k=2,
    )
    assert payload["outcomes"][0]["evidence_status"] == "NOT_READY"


def test_normalization_handles_turkish_i():
    assert (
        crosswalk.normalize_text("BİYOLOJİ")
        == "biyoloji"
    )


def test_validation_rejects_wrong_canonical_counts():
    payload = crosswalk.build_crosswalk(
        synthetic_registry(),
        synthetic_corpus(),
        top_k=2,
    )
    errors = crosswalk.validate_crosswalk(
        payload
    )
    assert errors
    assert any(
        "78" in error
        for error in errors
    )
