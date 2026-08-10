"""
Knowledge Factory V2 — Phase 5D Official Corpus Lexical Enrichment

Purpose:
Fetch each already-indexed official MEB/OGM basic-html page and build a
non-reconstructive lexical fingerprint for topic-source matching.

Important:
- Raw page prose is NOT persisted.
- Claims are NOT generated.
- Evidence is NOT marked READY.
- Only normalized lexical terms and short structural metadata are stored.
- Existing official corpus URL boundaries are preserved.

Input:
  data/knowledge/corpus/official_corpus_index.json

Output:
  data/knowledge/corpus/official_corpus_lexical_index.json
"""

import argparse
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CORPUS_INDEX_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "official_corpus_index.json"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "official_corpus_lexical_index.json"
)

ALLOWED_HOST = "ogmmateryal.eba.gov.tr"

DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_BASE_SECONDS = 1.0
DEFAULT_REQUEST_DELAY_SECONDS = 0.20

STOPWORDS = {
    "ve", "veya", "ile", "bir", "bu", "icin", "gibi",
    "olan", "olarak", "de", "da", "ki", "mi", "mu",
    "mı", "mü", "the", "and", "page", "sayfa",
}


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


def normalize_text(value):
    value = str(
        value or ""
    )

    value = (
        value.replace("İ", "I")
        .replace("ı", "i")
    )

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(
            char
        )
    )

    return value.casefold()


def lexical_tokens(value):
    found = re.findall(
        r"[a-z0-9]+",
        normalize_text(
            value
        ),
    )

    return [
        token
        for token in found
        if (
            len(token) >= 3
            and token not in STOPWORDS
        )
    ]


def validate_official_url(url):
    parsed = urlparse(
        url
    )

    if parsed.scheme != "https":
        raise ValueError(
            "Official corpus URL must use https."
        )

    if parsed.hostname != ALLOWED_HOST:
        raise ValueError(
            f"Unexpected corpus host: {parsed.hostname}"
        )

    return True


class VisibleTextParser(HTMLParser):
    """
    Extract visible text while excluding script/style/noscript/template.
    Raw text is held only in memory and is never written to disk.
    """

    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "template",
    }

    HEADING_TAGS = {
        "h1",
        "h2",
        "h3",
        "h4",
    }

    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.parts = []
        self.title_parts = []
        self.heading_parts = []
        self.in_title = False
        self.in_heading = False

    def handle_starttag(
        self,
        tag,
        attrs,
    ):
        tag = tag.casefold()

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return

        if tag == "title":
            self.in_title = True

        if tag in self.HEADING_TAGS:
            self.in_heading = True

    def handle_endtag(
        self,
        tag,
    ):
        tag = tag.casefold()

        if tag in self.SKIP_TAGS:
            if self.skip_depth > 0:
                self.skip_depth -= 1
            return

        if tag == "title":
            self.in_title = False

        if tag in self.HEADING_TAGS:
            self.in_heading = False

    def handle_data(
        self,
        data,
    ):
        if self.skip_depth:
            return

        text = " ".join(
            str(data).split()
        )

        if not text:
            return

        self.parts.append(
            text
        )

        if self.in_title:
            self.title_parts.append(
                text
            )

        if self.in_heading:
            self.heading_parts.append(
                text
            )

    def result(self):
        return {
            "visible_text": " ".join(
                self.parts
            ),
            "title": " ".join(
                self.title_parts
            ),
            "headings": " ".join(
                self.heading_parts
            ),
        }


def html_to_fingerprint(
    html,
    max_terms=400,
):
    parser = VisibleTextParser()
    parser.feed(
        html
    )

    parsed = parser.result()

    counts = Counter(
        lexical_tokens(
            parsed["visible_text"]
        )
    )

    # Deterministic ordering: descending frequency, then token.
    ranked = sorted(
        counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    terms = [
        token
        for token, count in ranked[
            :max_terms
        ]
    ]

    title_terms = sorted(
        set(
            lexical_tokens(
                parsed["title"]
            )
        )
    )

    heading_terms = sorted(
        set(
            lexical_tokens(
                parsed["headings"]
            )
        )
    )

    return {
        "terms": terms,
        "title_terms": title_terms,
        "heading_terms": heading_terms,
        "term_count": len(
            terms
        ),
    }


def _fetch_once(
    url,
    timeout=20,
):
    validate_official_url(
        url
    )

    request = urllib.request.Request(
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
        request,
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
                f"{url} | {exc}"
            )

            sleeper(
                wait_seconds
            )

    raise RuntimeError(
        "Official corpus enrichment fetch failed "
        f"after {max_retries} attempts: "
        f"{url} | {last_error}"
    )


def enrich_page(
    page,
    fetcher=fetch_text,
):
    url = page[
        "url"
    ]

    validate_official_url(
        url
    )

    result = dict(
        page
    )

    try:
        html = fetcher(
            url
        )

        fingerprint = html_to_fingerprint(
            html
        )

        result.update(
            fingerprint
        )

        result[
            "lexical_status"
        ] = "READY"

        return result

    except Exception as exc:
        result[
            "lexical_status"
        ] = "FAILED"
        result[
            "lexical_error"
        ] = str(
            exc
        )

        result[
            "terms"
        ] = []

        result[
            "title_terms"
        ] = []

        result[
            "heading_terms"
        ] = []

        return result


def enrich_index(
    corpus_index,
    fetcher=fetch_text,
):
    families = []

    total_pages = 0
    ready_pages = 0
    failed_pages = 0

    input_families = corpus_index.get(
        "families",
        [],
    )

    for family_position, family in enumerate(
        input_families,
        start=1,
    ):
        family_id = family[
            "family_id"
        ]

        pages = family.get(
            "pages",
            [],
        )

        print(
            f"[{family_position}/{len(input_families)}] "
            f"ENRICHING | {family_id} | "
            f"{len(pages)} pages"
        )

        enriched_pages = []

        for page_position, page in enumerate(
            pages,
            start=1,
        ):
            enriched = enrich_page(
                page,
                fetcher=fetcher,
            )

            enriched_pages.append(
                enriched
            )

            total_pages += 1

            if (
                enriched[
                    "lexical_status"
                ]
                == "READY"
            ):
                ready_pages += 1
            else:
                failed_pages += 1

            if (
                page_position % 25 == 0
                or page_position == len(
                    pages
                )
            ):
                print(
                    "  PROGRESS | "
                    f"{family_id} | "
                    f"{page_position}/{len(pages)}"
                )

        family_result = dict(
            family
        )

        family_result[
            "pages"
        ] = enriched_pages

        family_result[
            "lexical_ready_pages"
        ] = sum(
            1
            for page in enriched_pages
            if page[
                "lexical_status"
            ] == "READY"
        )

        family_result[
            "lexical_failed_pages"
        ] = sum(
            1
            for page in enriched_pages
            if page[
                "lexical_status"
            ] == "FAILED"
        )

        families.append(
            family_result
        )

    return {
        "version": "1.0",
        "kind": "OFFICIAL_CORPUS_LEXICAL_INDEX",
        "source_index_version": corpus_index.get(
            "version"
        ),
        "authority": corpus_index.get(
            "authority"
        ),
        "host": corpus_index.get(
            "host"
        ),
        "storage_policy": (
            "NON_RECONSTRUCTIVE_LEXICAL_FINGERPRINT"
        ),
        "family_count": len(
            families
        ),
        "total_pages": total_pages,
        "lexical_ready_pages": ready_pages,
        "lexical_failed_pages": failed_pages,
        "families": families,
        "unresolved_subjects": corpus_index.get(
            "unresolved_subjects",
            [],
        ),
    }


def print_summary(
    index,
):
    print("=" * 70)
    print(
        "KNOWLEDGE FACTORY V2 — "
        "PHASE 5D CORPUS LEXICAL ENRICHMENT"
    )
    print("=" * 70)

    print(
        f"Families      : "
        f"{index['family_count']}"
    )

    print(
        f"Total pages   : "
        f"{index['total_pages']}"
    )

    print(
        f"Lexical READY : "
        f"{index['lexical_ready_pages']}"
    )

    print(
        f"Lexical FAILED: "
        f"{index['lexical_failed_pages']}"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--corpus",
        default=str(
            CORPUS_INDEX_PATH
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT_PATH
        ),
    )

    args = parser.parse_args()

    corpus_index = load_json(
        args.corpus
    )

    enriched = enrich_index(
        corpus_index
    )

    write_json(
        args.output,
        enriched,
    )

    print_summary(
        enriched
    )

    print(
        f"LEXICAL INDEX | {args.output}"
    )

    if enriched[
        "lexical_failed_pages"
    ]:
        raise SystemExit(
            2
        )


if __name__ == "__main__":
    main()
