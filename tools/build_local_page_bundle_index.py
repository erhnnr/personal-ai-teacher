"""
Knowledge Factory V2 — Phase 6B Local Page Bundle Indexer

Builds a deterministic page-level corpus index from locally extracted
official MEB/MEBİ book packages.

Expected package layout:
  <package>/
    files/basic-html/pageN.html
    files/thumb/N.jpg

The indexer:
- ignores duplicate "(1)" style package folders when an equivalent canonical
  folder exists,
- extracts visible curriculum/material text from <pre><code>...</code></pre>,
- links each HTML page to its deterministic thumbnail,
- records missing text/image explicitly,
- does NOT create claims,
- does NOT mark evidence READY,
- does NOT OCR images.

Output:
  data/knowledge/corpus/local_page_bundle_index.json
"""

import argparse
import hashlib
import html
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ROOT = (
    PROJECT_ROOT
    / "local_corpus_extracted"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "local_page_bundle_index.json"
)

PACKAGE_MAP = {
    "tyt-matematik": ("MEBI-TYT-MATEMATIK", "TYT", "Matematik"),
    "tyt-turkce": ("MEBI-TYT-TURKCE", "TYT", "Türkçe"),
    "tyt-fizik": ("MEBI-TYT-FIZIK", "TYT", "Fizik"),
    "tyt-kimya": ("MEBI-TYT-KIMYA", "TYT", "Kimya"),
    "tyt-biyoloji": ("MEBI-TYT-BIYOLOJI", "TYT", "Biyoloji"),
    "tyt-tarih": ("MEBI-TYT-TARIH", "TYT", "Tarih"),
    "tyt-cografya": ("MEBI-TYT-COGRAFYA", "TYT", "Coğrafya"),
    "tyt-ayt-felsefe": ("MEBI-TYT-AYT-FELSEFE", "TYT_AYT", "Felsefe"),
    "ayt-matematik": ("MEBI-AYT-MATEMATIK", "AYT", "Matematik"),
    "ayt-fizik": ("MEBI-AYT-FIZIK", "AYT", "Fizik"),
    "ayt-kimya": ("MEBI-AYT-KIMYA", "AYT", "Kimya"),
    "ayt-biyoloji": ("MEBI-AYT-BIYOLOJI", "AYT", "Biyoloji"),
    "ayt-tarih": ("MEBI-AYT-TARIH", "AYT", "Tarih"),
    "ayt-cografya": ("MEBI-AYT-COGRAFYA", "AYT", "Coğrafya"),
    "ayt-tde": ("MEBI-AYT-TDE", "AYT", "Türk Dili ve Edebiyatı"),
    "ayt-mantik": ("MEBI-AYT-MANTIK", "AYT", "Mantık"),
    "ayt-psikoloji": ("MEBI-AYT-PSIKOLOJI", "AYT", "Psikoloji"),
    "ayt-sosyoloji": ("MEBI-AYT-SOSYOLOJI", "AYT", "Sosyoloji"),
    "ydt-ingilizce": ("MEBI-YDT-INGILIZCE", "YDT", "İngilizce"),
}


PAGE_RE = re.compile(
    r"^page(\d+)\.html$",
    flags=re.IGNORECASE,
)

PRE_CODE_RE = re.compile(
    r"<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>",
    flags=re.IGNORECASE | re.DOTALL,
)

TAG_RE = re.compile(
    r"<[^>]+>"
)


def normalize_package_name(name):
    return re.sub(
        r"\s+\(\d+\)$",
        "",
        str(name).strip().casefold(),
    )


def sha256_bytes(data):
    return hashlib.sha256(
        data
    ).hexdigest()


def extract_page_text(raw_html):
    matches = PRE_CODE_RE.findall(
        raw_html
    )

    if not matches:
        return ""

    parts = []

    for match in matches:
        cleaned = TAG_RE.sub(
            " ",
            match
        )

        cleaned = html.unescape(
            cleaned
        )

        cleaned = cleaned.replace(
            "\xa0",
            " ",
        )

        cleaned = re.sub(
            r"[ \t]+",
            " ",
            cleaned,
        )

        cleaned = re.sub(
            r"\n[ \t]+",
            "\n",
            cleaned,
        )

        cleaned = re.sub(
            r"\n{3,}",
            "\n\n",
            cleaned,
        )

        cleaned = cleaned.strip()

        if cleaned:
            parts.append(
                cleaned
            )

    return "\n\n".join(
        parts
    ).strip()


def page_number(path):
    match = PAGE_RE.match(
        Path(path).name
    )

    if not match:
        return None

    return int(
        match.group(
            1
        )
    )


def classify_package(folder):
    normalized = normalize_package_name(
        folder.name
    )

    metadata = PACKAGE_MAP.get(
        normalized
    )

    if metadata is None:
        return None

    package_id, exam, subject = metadata

    return {
        "package_id": package_id,
        "exam": exam,
        "subject": subject,
        "normalized_name": normalized,
    }


def discover_package_folders(root):
    root = Path(
        root
    )

    folders = sorted(
        [
            path
            for path in root.iterdir()
            if path.is_dir()
        ],
        key=lambda path: path.name.casefold(),
    )

    chosen = {}
    duplicates = []
    unknown = []

    for folder in folders:
        classification = classify_package(
            folder
        )

        if classification is None:
            unknown.append(
                folder.name
            )
            continue

        normalized = classification[
            "normalized_name"
        ]

        if normalized not in chosen:
            chosen[
                normalized
            ] = folder
            continue

        current = chosen[
            normalized
        ]

        current_is_duplicate_named = bool(
            re.search(
                r"\s+\(\d+\)$",
                current.name,
            )
        )

        candidate_is_duplicate_named = bool(
            re.search(
                r"\s+\(\d+\)$",
                folder.name,
            )
        )

        if (
            current_is_duplicate_named
            and not candidate_is_duplicate_named
        ):
            duplicates.append(
                current.name
            )

            chosen[
                normalized
            ] = folder
        else:
            duplicates.append(
                folder.name
            )

    return (
        sorted(
            chosen.values(),
            key=lambda path: path.name.casefold(),
        ),
        sorted(
            duplicates,
            key=str.casefold,
        ),
        sorted(
            unknown,
            key=str.casefold,
        ),
    )


def index_package(folder):
    metadata = classify_package(
        folder
    )

    if metadata is None:
        raise ValueError(
            f"Unknown package: {folder.name}"
        )

    html_root = (
        folder
        / "files"
        / "basic-html"
    )

    thumb_root = (
        folder
        / "files"
        / "thumb"
    )

    if not html_root.exists():
        raise FileNotFoundError(
            html_root
        )

    pages = []

    html_files = sorted(
        [
            path
            for path in html_root.glob(
                "page*.html"
            )
            if page_number(
                path
            ) is not None
        ],
        key=lambda path: page_number(
            path
        ),
    )

    for html_path in html_files:
        number = page_number(
            html_path
        )

        raw_bytes = html_path.read_bytes()

        raw_html = raw_bytes.decode(
            "utf-8",
            errors="replace",
        )

        text = extract_page_text(
            raw_html
        )

        thumb_path = (
            thumb_root
            / f"{number}.jpg"
        )

        image_exists = thumb_path.exists()

        pages.append(
            {
                "page": number,
                "html_path": str(
                    html_path.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "image_path": (
                    str(
                        thumb_path.relative_to(
                            PROJECT_ROOT
                        )
                    )
                    if image_exists
                    else None
                ),
                "source_anchor": (
                    f"{folder.name}/index.html#p={number}"
                ),
                "text": text,
                "text_status": (
                    "READY"
                    if text
                    else "EMPTY"
                ),
                "image_status": (
                    "READY"
                    if image_exists
                    else "MISSING"
                ),
                "html_sha256": sha256_bytes(
                    raw_bytes
                ),
            }
        )

    return {
        "package_id": metadata[
            "package_id"
        ],
        "exam": metadata[
            "exam"
        ],
        "subject": metadata[
            "subject"
        ],
        "source_folder": folder.name,
        "page_count": len(
            pages
        ),
        "text_ready_count": sum(
            1
            for item in pages
            if item[
                "text_status"
            ] == "READY"
        ),
        "text_empty_count": sum(
            1
            for item in pages
            if item[
                "text_status"
            ] == "EMPTY"
        ),
        "image_ready_count": sum(
            1
            for item in pages
            if item[
                "image_status"
            ] == "READY"
        ),
        "image_missing_count": sum(
            1
            for item in pages
            if item[
                "image_status"
            ] == "MISSING"
        ),
        "pages": pages,
    }


def build_index(root):
    (
        folders,
        duplicate_folders,
        unknown_folders,
    ) = discover_package_folders(
        root
    )

    packages = [
        index_package(
            folder
        )
        for folder in folders
    ]

    total_pages = sum(
        package[
            "page_count"
        ]
        for package in packages
    )

    text_ready = sum(
        package[
            "text_ready_count"
        ]
        for package in packages
    )

    text_empty = sum(
        package[
            "text_empty_count"
        ]
        for package in packages
    )

    image_ready = sum(
        package[
            "image_ready_count"
        ]
        for package in packages
    )

    image_missing = sum(
        package[
            "image_missing_count"
        ]
        for package in packages
    )

    return {
        "version": "1.0",
        "kind": "LOCAL_PAGE_BUNDLE_INDEX",
        "package_count": len(
            packages
        ),
        "duplicate_folder_count": len(
            duplicate_folders
        ),
        "unknown_folder_count": len(
            unknown_folders
        ),
        "total_pages": total_pages,
        "text_ready_pages": text_ready,
        "text_empty_pages": text_empty,
        "image_ready_pages": image_ready,
        "image_missing_pages": image_missing,
        "duplicates_ignored": duplicate_folders,
        "unknown_folders": unknown_folders,
        "packages": packages,
    }


def validate_index(index):
    errors = []

    if index[
        "package_count"
    ] != 19:
        errors.append(
            f"expected 19 unique packages, got "
            f"{index['package_count']}"
        )

    if index[
        "total_pages"
    ] != 2967:
        errors.append(
            f"expected 2967 unique pages, got "
            f"{index['total_pages']}"
        )

    if index[
        "duplicate_folder_count"
    ] != 1:
        errors.append(
            f"expected 1 duplicate folder, got "
            f"{index['duplicate_folder_count']}"
        )

    if index[
        "image_missing_pages"
    ] != 0:
        errors.append(
            f"expected 0 missing thumbnails, got "
            f"{index['image_missing_pages']}"
        )

    return errors


def write_json(path, data):
    path = Path(
        path
    )

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


def print_summary(index):
    print("=" * 72)
    print(
        "KNOWLEDGE FACTORY V2 — "
        "PHASE 6B LOCAL PAGE BUNDLE INDEX"
    )
    print("=" * 72)

    print(
        f"Packages       : {index['package_count']}"
    )

    print(
        f"Duplicates     : {index['duplicate_folder_count']}"
    )

    print(
        f"Unknown        : {index['unknown_folder_count']}"
    )

    print(
        f"Pages indexed  : {index['total_pages']}"
    )

    print(
        f"Text READY     : {index['text_ready_pages']}"
    )

    print(
        f"Text EMPTY     : {index['text_empty_pages']}"
    )

    print(
        f"Image linked   : {index['image_ready_pages']}"
    )

    print(
        f"Image missing  : {index['image_missing_pages']}"
    )

    for package in index[
        "packages"
    ]:
        print(
            f"  {package['package_id']:<24} | "
            f"{package['page_count']:>4} pages | "
            f"text={package['text_ready_count']:>4} | "
            f"image={package['image_ready_count']:>4}"
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        default=str(
            DEFAULT_ROOT
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT
        ),
    )

    args = parser.parse_args()

    index = build_index(
        args.root
    )

    errors = validate_index(
        index
    )

    write_json(
        args.output,
        index,
    )

    print_summary(
        index
    )

    if errors:
        print(
            "INDEX VALIDATION: FAIL"
        )

        for error in errors:
            print(
                f"  - {error}"
            )

        raise SystemExit(
            2
        )

    print(
        "INDEX VALIDATION: PASS"
    )

    print(
        f"INDEX          | {args.output}"
    )


if __name__ == "__main__":
    main()
