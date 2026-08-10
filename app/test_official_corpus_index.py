import sys
from pathlib import Path
import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_official_corpus_index as corpus


def family():
    return {
        "family_id": "MEBI-TYT-MATEMATIK",
        "exam": "TYT",
        "subject": "Matematik",
        "base_url": "https://ogmmateryal.eba.gov.tr/kitap/mebi-konu-ozetleri/tyt-matematik/files/basic-html/",
        "index_url": "https://ogmmateryal.eba.gov.tr/kitap/mebi-konu-ozetleri/tyt-matematik/files/basic-html/index.html",
    }


def test_extract_page_numbers_is_sorted_and_unique():
    html = """
    <a href="page3.html">3</a>
    <a href="page1.html">1</a>
    <a href="page3.html">3</a>
    <a href="page2.html">2</a>
    """
    assert corpus.extract_page_numbers(html) == [1, 2, 3]


def test_official_host_is_enforced():
    with pytest.raises(ValueError, match="Unexpected corpus host"):
        corpus.validate_official_url(
            "https://example.com/page1.html"
        )


def test_family_index_builds_only_discovered_pages():
    html = """
    <a href="page1.html">1</a>
    <a href="page2.html">2</a>
    <a href="page9.html">9</a>
    """
    result = corpus.index_family(
        family(),
        fetcher=lambda url: html,
    )

    assert result["status"] == "INDEXED"
    assert result["page_count"] == 3
    assert [p["page"] for p in result["pages"]] == [1, 2, 9]
    assert all(p["official"] is True for p in result["pages"])


def test_fetch_failure_is_explicit():
    def broken(url):
        raise RuntimeError("network down")

    result = corpus.index_family(
        family(),
        fetcher=broken,
    )

    assert result["status"] == "FAILED"
    assert result["page_count"] == 0
    assert "network down" in result["error"]


def test_build_index_counts_results():
    data = {
        "families": [
            family(),
            {
                **family(),
                "family_id": "MEBI-TYT-FIZIK",
                "subject": "Fizik",
            },
        ],
        "unresolved_subjects": [],
    }

    def fake_fetch(url):
        return '<a href="page1.html">1</a><a href="page2.html">2</a>'

    index = corpus.build_index(
        data,
        fetcher=fake_fetch,
    )

    assert index["family_count"] == 2
    assert index["indexed_family_count"] == 2
    assert index["failed_family_count"] == 0
    assert index["total_pages"] == 4
