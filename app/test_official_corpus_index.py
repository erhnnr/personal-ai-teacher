"""
Knowledge Factory V2 — Phase 5B.1 corpus completeness tests.
"""

import sys
from pathlib import Path

import pytest


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

import build_official_corpus_index as corpus


def family():
    return {
        "family_id": "MEBI-TYT-FIZIK",
        "exam": "TYT",
        "subject": "Fizik",
        "base_url": (
            "https://ogmmateryal.eba.gov.tr/"
            "kitap/mebi-konu-ozetleri/"
            "tyt-fizik/files/basic-html/"
        ),
        "index_url": (
            "https://ogmmateryal.eba.gov.tr/"
            "kitap/mebi-konu-ozetleri/"
            "tyt-fizik/files/basic-html/"
            "index.html"
        ),
    }


def html_links(
    start,
    end,
):
    return "".join(
        (
            f'<a href="page'
            f'{number}.html">'
            f'{number}</a>'
        )
        for number in range(
            start,
            end + 1,
        )
    )


def test_extract_page_numbers_is_sorted_and_unique():
    html = (
        '<a href="page3.html">3</a>'
        '<a href="page1.html">1</a>'
        '<a href="page3.html">3</a>'
        '<a href="page2.html">2</a>'
    )

    assert (
        corpus.extract_page_numbers(
            html
        )
        == [
            1,
            2,
            3,
        ]
    )


def test_official_host_is_enforced():
    with pytest.raises(
        ValueError,
        match="Unexpected corpus host",
    ):
        corpus.validate_official_url(
            "https://example.com/page1.html"
        )


def test_frontier_discovers_beyond_first_ten_pages():
    fam = family()

    def fake_fetch(
        url,
    ):
        if url.endswith(
            "index.html"
        ):
            return html_links(
                1,
                10,
            )

        if url.endswith(
            "page10.html"
        ):
            return html_links(
                5,
                15,
            )

        if url.endswith(
            "page15.html"
        ):
            return html_links(
                10,
                20,
            )

        if url.endswith(
            "page20.html"
        ):
            return html_links(
                15,
                20,
            )

        raise AssertionError(
            f"Unexpected URL: {url}"
        )

    numbers = (
        corpus.discover_page_numbers(
            fam["index_url"],
            fam["base_url"],
            fetcher=fake_fetch,
        )
    )

    assert numbers == list(
        range(
            1,
            21,
        )
    )


def test_non_contiguous_discovery_is_rejected():
    fam = family()

    def fake_fetch(
        url,
    ):
        if url.endswith(
            "index.html"
        ):
            return (
                '<a href="page1.html">1</a>'
                '<a href="page3.html">3</a>'
            )

        if url.endswith(
            "page3.html"
        ):
            return (
                '<a href="page1.html">1</a>'
                '<a href="page3.html">3</a>'
            )

        raise AssertionError(
            f"Unexpected URL: {url}"
        )

    with pytest.raises(
        ValueError,
        match="non-contiguous",
    ):
        corpus.discover_page_numbers(
            fam["index_url"],
            fam["base_url"],
            fetcher=fake_fetch,
        )


def test_family_index_uses_complete_discovery():
    fam = family()

    def fake_fetch(
        url,
    ):
        if url.endswith(
            "index.html"
        ):
            return html_links(
                1,
                10,
            )

        if url.endswith(
            "page10.html"
        ):
            return html_links(
                5,
                12,
            )

        if url.endswith(
            "page12.html"
        ):
            return html_links(
                7,
                12,
            )

        raise AssertionError(
            f"Unexpected URL: {url}"
        )

    result = corpus.index_family(
        fam,
        fetcher=fake_fetch,
    )

    assert (
        result["status"]
        == "INDEXED"
    )

    assert (
        result["page_count"]
        == 12
    )

    assert (
        result["max_page"]
        == 12
    )


def test_fetch_failure_is_explicit():
    def broken(
        url,
    ):
        raise RuntimeError(
            "network down"
        )

    result = corpus.index_family(
        family(),
        fetcher=broken,
    )

    assert (
        result["status"]
        == "FAILED"
    )

    assert (
        result["page_count"]
        == 0
    )

    assert (
        "network down"
        in result["error"]
    )


def test_build_index_counts_complete_pages():
    data = {
        "families": [
            family(),
            {
                **family(),
                "family_id": (
                    "MEBI-TYT-MATEMATIK"
                ),
                "subject": "Matematik",
            },
        ],
        "unresolved_subjects": [],
    }

    def fake_fetch(
        url,
    ):
        if url.endswith(
            "index.html"
        ):
            return html_links(
                1,
                3,
            )

        if url.endswith(
            "page3.html"
        ):
            return html_links(
                1,
                3,
            )

        raise AssertionError(
            f"Unexpected URL: {url}"
        )

    index = corpus.build_index(
        data,
        fetcher=fake_fetch,
    )

    assert (
        index["family_count"]
        == 2
    )

    assert (
        index["indexed_family_count"]
        == 2
    )

    assert (
        index["failed_family_count"]
        == 0
    )

    assert (
        index["total_pages"]
        == 6
    )

    assert (
        index["discovery_mode"]
        == "PAGINATION_FRONTIER_RETRY"
    )
