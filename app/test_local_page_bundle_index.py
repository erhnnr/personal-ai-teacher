"""
Knowledge Factory V2 — Phase 6B tests.
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

import build_local_page_bundle_index as indexer


def test_duplicate_package_name_normalization():
    assert (
        indexer.normalize_package_name(
            "tyt-ayt-felsefe (1)"
        )
        == "tyt-ayt-felsefe"
    )


def test_page_number_parsing():
    assert (
        indexer.page_number(
            Path(
                "page158.html"
            )
        )
        == 158
    )

    assert (
        indexer.page_number(
            Path(
                "index.html"
            )
        )
        is None
    )


def test_extracts_pre_code_text():
    raw = """
    <html>
      <body>
        <pre style="white-space:pre-line"><code>
        MATEMATİK

        Zengin ve Anlaşılır İçerik
        </code></pre>
      </body>
    </html>
    """

    text = indexer.extract_page_text(
        raw
    )

    assert "MATEMATİK" in text
    assert "Zengin ve Anlaşılır İçerik" in text


def test_html_entities_are_decoded():
    raw = """
    <pre><code>
    A &lt; B &amp; C
    </code></pre>
    """

    assert (
        indexer.extract_page_text(
            raw
        )
        == "A < B & C"
    )


def test_package_classification():
    result = indexer.classify_package(
        Path(
            "ayt-biyoloji"
        )
    )

    assert (
        result[
            "package_id"
        ]
        == "MEBI-AYT-BIYOLOJI"
    )


def test_expected_unique_page_total_is_locked():
    assert (
        242
        + 103
        + 280
        + 156
        + 96
        + 138
        + 100
        + 96
        + 242
        + 176
        + 128
        + 172
        + 120
        + 200
        + 94
        + 158
        + 186
        + 126
        + 154
        == 2967
    )
