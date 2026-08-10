"""
Knowledge Factory V2 — Phase 5B.2 Resilient Official Corpus Indexer

Adds polite request pacing, retry/backoff, and progress output to the
Phase 5B.1 pagination-frontier discovery.

The server may occasionally reset connections (WinError 10054). Such
transport failures are retried; semantic/indexing failures are not hidden.
"""

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = PROJECT_ROOT / "data" / "knowledge" / "corpus"
FAMILY_PATH = CORPUS_ROOT / "official_corpus_families.json"
DEFAULT_INDEX_PATH = CORPUS_ROOT / "official_corpus_index.json"

ALLOWED_HOST = "ogmmateryal.eba.gov.tr"
MAX_DISCOVERY_STEPS = 2000

DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_BASE_SECONDS = 1.0
DEFAULT_REQUEST_DELAY_SECONDS = 0.35


def load_json(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def validate_official_url(url):
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError(
            "Official corpus URL must use https."
        )

    if parsed.hostname != ALLOWED_HOST:
        raise ValueError(
            f"Unexpected corpus host: {parsed.hostname}"
        )

    return True


def _fetch_once(
    url,
    timeout=20,
):
    validate_official_url(
        url
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(compatible; Personal-AI-Teacher/"
                "KnowledgeFactory-2.0)"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Connection": "close",
        },
    )

    with urllib.request.urlopen(
        req,
        timeout=timeout,
    ) as response:
        charset = (
            response.headers.get_content_charset()
            or "utf-8"
        )

        return response.read().decode(
            charset,
            errors="replace",
        )


def fetch_text(
    url,
    timeout=20,
    max_retries=DEFAULT_MAX_RETRIES,
    retry_base_seconds=DEFAULT_RETRY_BASE_SECONDS,
    request_delay_seconds=DEFAULT_REQUEST_DELAY_SECONDS,
    sleeper=time.sleep,
):
    """
    Retry transient transport/server failures with exponential backoff.
    URL validation and non-transient semantic errors remain explicit.
    """

    validate_official_url(
        url
    )

    last_error = None

    for attempt in range(
        1,
        max_retries + 1,
    ):
        try:
            if request_delay_seconds > 0:
                sleeper(
                    request_delay_seconds
                )

            return _fetch_once(
                url,
                timeout=timeout,
            )

        except (
            urllib.error.URLError,
            ConnectionResetError,
            TimeoutError,
            OSError,
        ) as exc:
            last_error = exc

            if attempt >= max_retries:
                break

            wait_seconds = (
                retry_base_seconds
                * (2 ** (attempt - 1))
            )

            print(
                "RETRY FETCH | "
                f"{attempt + 1}/{max_retries} | "
                f"{url} | "
                f"{exc}"
            )

            sleeper(
                wait_seconds
            )

    raise RuntimeError(
        "Official corpus fetch failed after "
        f"{max_retries} attempts: {url} | "
        f"{last_error}"
    )


def extract_page_numbers(html):
    numbers = {
        int(value)
        for value in re.findall(
            r'page(\d+)\.html',
            html,
            flags=re.IGNORECASE,
        )
    }

    return sorted(
        number
        for number in numbers
        if number > 0
    )


def page_url(
    base_url,
    page_number,
):
    return urljoin(
        base_url,
        f"page{page_number}.html",
    )


def discover_page_numbers(
    index_url,
    base_url,
    fetcher=fetch_text,
):
    validate_official_url(
        index_url
    )
    validate_official_url(
        base_url
    )

    index_html = fetcher(
        index_url
    )

    initial = extract_page_numbers(
        index_html
    )

    if not initial:
        raise ValueError(
            "No pageN.html links discovered "
            "from corpus index."
        )

    discovered = set(
        initial
    )

    visited_probes = set()
    probe = max(
        discovered
    )

    steps = 0

    while True:
        steps += 1

        if steps > MAX_DISCOVERY_STEPS:
            raise RuntimeError(
                "Corpus pagination discovery "
                "exceeded safety limit."
            )

        if probe in visited_probes:
            break

        visited_probes.add(
            probe
        )

        html = fetcher(
            page_url(
                base_url,
                probe,
            )
        )

        found = extract_page_numbers(
            html
        )

        if not found:
            break

        discovered.update(
            found
        )

        new_probe = max(
            discovered
        )

        if new_probe <= probe:
            break

        probe = new_probe

    numbers = sorted(
        discovered
    )

    expected = set(
        range(
            1,
            max(numbers) + 1,
        )
    )

    missing = sorted(
        expected
        - set(numbers)
    )

    if missing:
        preview = ", ".join(
            str(value)
            for value in missing[:10]
        )

        raise ValueError(
            "Corpus pagination discovery is "
            f"non-contiguous. Missing: {preview}"
        )

    return numbers


def index_family(
    family,
    fetcher=fetch_text,
):
    index_url = family[
        "index_url"
    ]
    base_url = family[
        "base_url"
    ]

    result = {
        "family_id": family[
            "family_id"
        ],
        "exam": family[
            "exam"
        ],
        "subject": family[
            "subject"
        ],
        "status": "FAILED",
        "index_url": index_url,
        "page_count": 0,
        "max_page": 0,
        "pages": [],
    }

    try:
        page_numbers = (
            discover_page_numbers(
                index_url,
                base_url,
                fetcher=fetcher,
            )
        )

        result["pages"] = [
            {
                "page": number,
                "url": page_url(
                    base_url,
                    number,
                ),
                "source_kind": (
                    "MEBI_KONU_OZETI_PAGE"
                ),
                "official": True,
            }
            for number in page_numbers
        ]

        result[
            "page_count"
        ] = len(
            result["pages"]
        )

        result[
            "max_page"
        ] = max(
            page_numbers
        )

        result[
            "status"
        ] = "INDEXED"

        return result

    except Exception as exc:
        result[
            "error"
        ] = str(
            exc
        )

        return result


def build_index(
    families_data,
    fetcher=fetch_text,
):
    indexed = []

    families = families_data.get(
        "families",
        [],
    )

    for position, family in enumerate(
        families,
        start=1,
    ):
        family_id = family[
            "family_id"
        ]

        print(
            f"[{position}/{len(families)}] "
            f"SCANNING | {family_id}"
        )

        result = index_family(
            family,
            fetcher=fetcher,
        )

        indexed.append(
            result
        )

        if result[
            "status"
        ] == "INDEXED":
            print(
                "FOUND    | "
                f"{family_id} | "
                f"{result['page_count']} pages"
            )
        else:
            print(
                "FAILED   | "
                f"{family_id} | "
                f"{result.get('error')}"
            )

    return {
        "version": "1.2",
        "kind": "OFFICIAL_CORPUS_INDEX",
        "authority": (
            "Millî Eğitim Bakanlığı / "
            "OGM Materyal / MEBİ"
        ),
        "host": ALLOWED_HOST,
        "discovery_mode": (
            "PAGINATION_FRONTIER_RETRY"
        ),
        "family_count": len(
            indexed
        ),
        "indexed_family_count": sum(
            1
            for item in indexed
            if item["status"] == "INDEXED"
        ),
        "failed_family_count": sum(
            1
            for item in indexed
            if item["status"] == "FAILED"
        ),
        "total_pages": sum(
            item["page_count"]
            for item in indexed
        ),
        "families": indexed,
        "unresolved_subjects": (
            families_data.get(
                "unresolved_subjects",
                [],
            )
        ),
    }


def print_summary(
    index,
):
    print("=" * 70)
    print(
        "KNOWLEDGE FACTORY V2 — "
        "PHASE 5B.2 RESILIENT CORPUS INDEX"
    )
    print("=" * 70)

    print(
        f"Families      : "
        f"{index['family_count']}"
    )

    print(
        f"Indexed       : "
        f"{index['indexed_family_count']}"
    )

    print(
        f"Failed        : "
        f"{index['failed_family_count']}"
    )

    print(
        f"Total pages   : "
        f"{index['total_pages']}"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--families",
        default=str(
            FAMILY_PATH
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_INDEX_PATH
        ),
    )

    args = parser.parse_args()

    families_data = load_json(
        args.families
    )

    index = build_index(
        families_data
    )

    write_json(
        args.output,
        index,
    )

    print_summary(
        index
    )

    print(
        f"INDEX         | {args.output}"
    )

    if index[
        "failed_family_count"
    ]:
        raise SystemExit(
            2
        )


if __name__ == "__main__":
    main()
