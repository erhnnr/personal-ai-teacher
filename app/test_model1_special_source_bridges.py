import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import model1_official_source_context as source_context


def _page(number, text):
    return {
        "page": number,
        "text_status": "READY",
        "text": text * 8,
        "source_anchor": f"page-{number}",
        "html_path": f"page{number}.html",
    }


def _fake_packages():
    return {
        "MEBI-TYT-MATEMATIK": {
            "package_id": "MEBI-TYT-MATEMATIK",
            "pages": [
                _page(55, "Verileri belirleme liste tablo sistematik düşünme akıl yürütme. "),
                _page(60, "Koşullu önerme ise bağlacı hipotez hüküm gerektirme. "),
                _page(70, "Saymanın temel ilkesi ve sayma yöntemleri. "),
                _page(71, "Faktöriyel kavramı ve işlemleri. "),
                _page(72, "Permütasyon sıralama ve farklı dizilişler. "),
                _page(74, "Kombinasyon kavramı ve seçim. "),
                _page(77, "Binom açılımı Pascal üçgeni. "),
            ],
        },
        "MEBI-TYT-TURKCE": {
            "package_id": "MEBI-TYT-TURKCE",
            "pages": [
                _page(33, "Paragraf oluşturma cümleleri anlamlı sıraya koyma kronolojik sıra. "),
                _page(118, "Mantık hatası sıralama yanlışları tutarlılık anlam belirsizliği. "),
            ],
        },
    }


def test_ayt_permutation_combination_binomial_uses_reviewed_tyt_math_bridge(
    monkeypatch,
):
    monkeypatch.setattr(
        source_context,
        "package_index",
        _fake_packages,
    )

    record = {
        "exam": "AYT",
        "subject": "Matematik",
        "topic": "Permütasyon Kombinasyon ve Binom",
        "subtopics": [
            "Sayma yöntemleri",
            "Faktöriyel",
            "Permütasyon",
            "Kombinasyon",
            "Binom açılımı",
            "Pascal üçgeni",
        ],
    }

    sources = source_context.resolve_official_sources(
        record,
        allow_network=False,
    )

    assert [item["page"] for item in sources] == [70, 71, 72, 74, 77]
    assert all(
        item["package_id"] == "MEBI-TYT-MATEMATIK"
        for item in sources
    )
    assert all(
        item["source_kind"]
        == "LOCAL_MEBI_REVIEWED_CROSS_FAMILY_BRIDGE"
        for item in sources
    )


def test_tyt_verbal_reasoning_uses_composite_official_bridge(
    monkeypatch,
):
    monkeypatch.setattr(
        source_context,
        "package_index",
        _fake_packages,
    )

    record = {
        "exam": "TYT",
        "subject": "Türkçe",
        "topic": "Sözel Mantık ve Muhakeme",
        "subtopics": [
            "Bilgi sıralama",
            "Koşullu çıkarım",
            "Tablo oluşturma",
            "Şema yorumlama",
            "Metinden mantıksal sonuç çıkarma",
        ],
    }

    sources = source_context.resolve_official_sources(
        record,
        allow_network=False,
    )

    assert [
        (item["package_id"], item["page"])
        for item in sources
    ] == [
        ("MEBI-TYT-TURKCE", 33),
        ("MEBI-TYT-TURKCE", 118),
        ("MEBI-TYT-MATEMATIK", 55),
        ("MEBI-TYT-MATEMATIK", 60),
    ]


def test_special_bridge_fails_closed_if_local_pages_are_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        source_context,
        "package_index",
        lambda: {},
    )

    record = {
        "exam": "AYT",
        "subject": "Matematik",
        "topic": "Permütasyon Kombinasyon ve Binom",
        "subtopics": [],
    }

    assert (
        source_context.resolve_official_sources(
            record,
            allow_network=False,
        )
        == []
    )
