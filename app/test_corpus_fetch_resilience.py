"""
Phase 5B.2 resilient fetch tests.
"""

import sys
import urllib.error
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


def test_fetch_retries_transient_reset(
    monkeypatch,
):
    calls = {
        "count": 0,
    }

    def fake_once(
        url,
        timeout=20,
    ):
        calls[
            "count"
        ] += 1

        if calls[
            "count"
        ] < 3:
            raise ConnectionResetError(
                "reset"
            )

        return "<html>ok</html>"

    monkeypatch.setattr(
        corpus,
        "_fetch_once",
        fake_once,
    )

    sleeps = []

    result = corpus.fetch_text(
        (
            "https://ogmmateryal.eba.gov.tr/"
            "x/index.html"
        ),
        max_retries=5,
        retry_base_seconds=0.01,
        request_delay_seconds=0,
        sleeper=sleeps.append,
    )

    assert result == "<html>ok</html>"
    assert calls["count"] == 3
    assert sleeps == [
        0.01,
        0.02,
    ]


def test_fetch_stops_after_retry_budget(
    monkeypatch,
):
    def fake_once(
        url,
        timeout=20,
    ):
        raise urllib.error.URLError(
            "down"
        )

    monkeypatch.setattr(
        corpus,
        "_fetch_once",
        fake_once,
    )

    with pytest.raises(
        RuntimeError,
        match="after 3 attempts",
    ):
        corpus.fetch_text(
            (
                "https://ogmmateryal.eba.gov.tr/"
                "x/index.html"
            ),
            max_retries=3,
            retry_base_seconds=0,
            request_delay_seconds=0,
            sleeper=lambda value: None,
        )


def test_progress_build_index_counts_success(
    capsys,
):
    data = {
        "families": [
            {
                "family_id": "F1",
                "exam": "TYT",
                "subject": "Fizik",
                "base_url": (
                    "https://ogmmateryal.eba.gov.tr/x/"
                ),
                "index_url": (
                    "https://ogmmateryal.eba.gov.tr/"
                    "x/index.html"
                ),
            }
        ],
        "unresolved_subjects": [],
    }

    def fake_fetch(
        url,
    ):
        if url.endswith(
            "index.html"
        ):
            return (
                '<a href="page1.html">1</a>'
                '<a href="page2.html">2</a>'
            )

        return (
            '<a href="page1.html">1</a>'
            '<a href="page2.html">2</a>'
        )

    result = corpus.build_index(
        data,
        fetcher=fake_fetch,
    )

    output = capsys.readouterr().out

    assert "SCANNING | F1" in output
    assert "FOUND    | F1 | 2 pages" in output
    assert result["indexed_family_count"] == 1
    assert result["total_pages"] == 2
