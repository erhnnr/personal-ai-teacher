
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_curriculum_corpus_crosswalk as crosswalk


def page(package_id, number, text):
    return {
        "package_id": package_id,
        "page": number,
        "text": text,
        "text_status": "READY",
        "image_status": "LINKED",
        "html_path": None,
        "image_path": None,
        "source_anchor": None,
    }


def outcome(grade=12):
    return {
        "id": "BİY.12.2.2",
        "grade": grade,
        "theme_number": 2,
        "theme_name": "Gen",
        "theme_content_framework": (
            "Nükleik Asitler DNA RNA Replikasyon "
            "Transkripsiyon Translasyon Genetik Kalıtım"
        ),
        "title": "DNA replikasyonunun bilimsel modelini oluşturabilme",
        "source_page": 79,
    }


def test_framework_only_page_is_not_candidate():
    pages = [
        page(
            "MEBI-AYT-BIYOLOJI",
            8,
            "genetik kalıtım transkripsiyon translasyon",
        )
    ]
    index, df = crosswalk.build_page_index(pages)
    candidates = crosswalk.rank_candidates(
        outcome(), index, df, top_k=5
    )
    assert candidates == []


def test_specific_title_page_beats_broad_index_page():
    pages = [
        page(
            "MEBI-AYT-BIYOLOJI",
            8,
            "genetik kalıtım dna transkripsiyon translasyon biyoteknoloji",
        ),
        page(
            "MEBI-AYT-BIYOLOJI",
            170,
            "DNA replikasyonunun aşamaları ve replikasyon modeli",
        ),
    ]
    index, df = crosswalk.build_page_index(pages)
    candidates = crosswalk.rank_candidates(
        outcome(), index, df, top_k=2
    )
    assert candidates[0]["page"] == 170


def test_grade_package_affinity_prefers_tyt_for_grade_9():
    out = {
        **outcome(grade=9),
        "id": "BİY.9.1.5",
        "title": "Canlıları sınıflandırabilme",
        "theme_name": "Yaşam",
        "theme_content_framework": "Sınıflandırma Biyoçeşitlilik",
    }
    pages = [
        page(
            "MEBI-TYT-BIYOLOJI",
            73,
            "Canlıları sınıflandırabilme modern sınıflandırma",
        ),
        page(
            "MEBI-AYT-BIYOLOJI",
            73,
            "Canlıları sınıflandırabilme modern sınıflandırma",
        ),
    ]
    index, df = crosswalk.build_page_index(pages)
    candidates = crosswalk.rank_candidates(
        out, index, df, top_k=2
    )
    assert candidates[0]["package_id"] == "MEBI-TYT-BIYOLOJI"


def test_single_title_hit_is_not_strong():
    candidates = [
        {
            "score": 100.0,
            "title_hits": ["genetik"],
            "title_bigrams": [],
            "package_affinity": True,
        },
        {
            "score": 10.0,
            "title_hits": ["kalıtım"],
            "title_bigrams": [],
            "package_affinity": True,
        },
    ]
    assert crosswalk.classify_candidate_set(candidates) == "REVIEW_REQUIRED"


def test_strong_requires_specific_support():
    candidates = [
        {
            "score": 100.0,
            "title_hits": ["dna", "replikasyonunun", "modelini"],
            "title_bigrams": ["dna replikasyonunun"],
            "package_affinity": True,
        },
        {
            "score": 90.0,
            "title_hits": ["dna", "modelini"],
            "title_bigrams": [],
            "package_affinity": True,
        },
    ]
    assert crosswalk.classify_candidate_set(candidates) == "STRONG_CANDIDATE"
