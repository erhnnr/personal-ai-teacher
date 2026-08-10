"""
Knowledge Factory V2 — Phase 6A Official Curriculum Registry tests.
"""

import sys
from pathlib import Path


TOOLS = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "tools"
)

if str(TOOLS) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS),
    )

import build_official_curriculum_registry as registry


def test_normalize_joins_pdf_hyphen_breaks():
    assert (
        registry.normalize_pdf_text(
            "devamlı-\nlığı"
        )
        == "devamlılığı"
    )


def test_outcome_title_extraction():
    block = """
    BİY.10.1.3. Fotosentez ile ilgili deney yapabilme
    a) Deney düzeneği oluşturur.
    b) Gözlem yapar.
    İÇERİK ÇERÇEVESİ Fotosentez
    Anahtar Kavramlar klorofil
    """

    assert (
        registry.extract_outcome_title(
            block
        )
        == "Fotosentez ile ilgili deney yapabilme"
    )


def test_content_and_key_concepts_extraction():
    block = """
    BİY.12.2.1. Nükleik asitlerin rolünü sorgulayabilme
    a) Soru sorar.
    İÇERİK ÇERÇEVESİ Nükleik Asitler ve Gen İfadesi
    DNA ve RNA'nın Moleküler Yapısı
    Anahtar Kavramlar DNA replikasyonu, gen ifadesi
    ÖĞRENME KANITLARI
    çalışma yaprağı
    """

    assert (
        registry.extract_content_framework(
            block
        )
        == (
            "Nükleik Asitler ve Gen İfadesi "
            "DNA ve RNA'nın Moleküler Yapısı"
        )
    )

    assert (
        registry.extract_key_concepts(
            block
        )
        == "DNA replikasyonu, gen ifadesi"
    )


def test_duplicate_outcome_keeps_richer_record():
    full_text = """
    [[PAGE:13]]
    BİY.9.1.1. Kısa başlık
    a) x
    İÇERİK ÇERÇEVESİ Yaşam
    [[PAGE:14]]
    BİY.9.1.1. Biyolojideki dönüm noktalarının insan hayatına katkılarını sorgulayabilme
    a) Katkıları belirtir.
    İÇERİK ÇERÇEVESİ Yaşam Bilimi: Biyoloji
    Sınıflandırma ve Biyoçeşitlilik
    Anahtar Kavramlar bilimsel yöntem, bilim etiği
    """

    outcomes = registry.split_outcome_blocks(
        full_text
    )

    assert len(
        outcomes
    ) == 1

    assert outcomes[
        0
    ][
        "source_page"
    ] == 14

    assert "dönüm noktalarının" in outcomes[
        0
    ][
        "title"
    ]


def test_expected_biology_curriculum_totals_are_locked():
    assert registry.EXPECTED_OUTCOME_COUNTS == {
        9: 15,
        10: 19,
        11: 22,
        12: 22,
    }

    assert sum(
        registry.EXPECTED_OUTCOME_COUNTS.values()
    ) == 78


def test_expected_theme_map_is_locked():
    assert registry.EXPECTED_THEMES[
        9
    ] == {
        1: "Yaşam",
        2: "Organizasyon",
    }

    assert registry.EXPECTED_THEMES[
        12
    ] == {
        1: "Üreme",
        2: "Gen",
    }
