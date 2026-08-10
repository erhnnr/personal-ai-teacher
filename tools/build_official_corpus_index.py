"""
Knowledge Factory V2 — Phase 5B Official Corpus Indexer

Builds a machine-readable index of official MEB/OGM MEBİ konu-özeti
page URLs. It does not create claims and does not mark evidence READY.

Network behavior:
- fetch only configured official OGM pages;
- discover pageN.html links from each family index;
- save page URLs as source candidates;
- failures remain explicit and do not fabricate pages.
"""

import argparse
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = PROJECT_ROOT / "data" / "knowledge" / "corpus"
FAMILY_PATH = CORPUS_ROOT / "official_corpus_families.json"
DEFAULT_INDEX_PATH = CORPUS_ROOT / "official_corpus_index.json"

ALLOWED_HOST = "ogmmateryal.eba.gov.tr"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def validate_official_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Official corpus URL must use https.")
    if parsed.hostname != ALLOWED_HOST:
        raise ValueError(f"Unexpected corpus host: {parsed.hostname}")
    return True


def fetch_text(url, timeout=20):
    validate_official_url(url)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Personal-AI-Teacher-KnowledgeFactory/2.0"
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_page_numbers(html):
    numbers = {
        int(value)
        for value in re.findall(
            r'(?:href=["\'][^"\']*)?page(\d+)\.html',
            html,
            flags=re.IGNORECASE,
        )
    }
    return sorted(numbers)


def index_family(family, fetcher=fetch_text):
    index_url = family["index_url"]
    base_url = family["base_url"]

    validate_official_url(index_url)
    validate_official_url(base_url)

    result = {
        "family_id": family["family_id"],
        "exam": family["exam"],
        "subject": family["subject"],
        "status": "FAILED",
        "index_url": index_url,
        "page_count": 0,
        "pages": [],
    }

    try:
        html = fetcher(index_url)
        page_numbers = extract_page_numbers(html)

        if not page_numbers:
            result["error"] = "No pageN.html links discovered."
            return result

        result["pages"] = [
            {
                "page": number,
                "url": urljoin(
                    base_url,
                    f"page{number}.html",
                ),
                "source_kind": "MEBI_KONU_OZETI_PAGE",
                "official": True,
            }
            for number in page_numbers
        ]

        result["page_count"] = len(result["pages"])
        result["status"] = "INDEXED"
        return result

    except Exception as exc:
        result["error"] = str(exc)
        return result


def build_index(families_data, fetcher=fetch_text):
    indexed = [
        index_family(family, fetcher=fetcher)
        for family in families_data.get("families", [])
    ]

    return {
        "version": "1.0",
        "kind": "OFFICIAL_CORPUS_INDEX",
        "authority": "Millî Eğitim Bakanlığı / OGM Materyal / MEBİ",
        "host": ALLOWED_HOST,
        "family_count": len(indexed),
        "indexed_family_count": sum(
            1 for item in indexed if item["status"] == "INDEXED"
        ),
        "failed_family_count": sum(
            1 for item in indexed if item["status"] == "FAILED"
        ),
        "total_pages": sum(item["page_count"] for item in indexed),
        "families": indexed,
        "unresolved_subjects": families_data.get(
            "unresolved_subjects",
            [],
        ),
    }


def print_summary(index):
    print("=" * 70)
    print("KNOWLEDGE FACTORY V2 — PHASE 5B OFFICIAL CORPUS INDEXER")
    print("=" * 70)
    print(f"Families      : {index['family_count']}")
    print(f"Indexed       : {index['indexed_family_count']}")
    print(f"Failed        : {index['failed_family_count']}")
    print(f"Total pages   : {index['total_pages']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--families",
        default=str(FAMILY_PATH),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_INDEX_PATH),
    )
    args = parser.parse_args()

    families_data = load_json(args.families)
    index = build_index(families_data)
    write_json(args.output, index)
    print_summary(index)
    print(f"INDEX         | {args.output}")

    if index["failed_family_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
