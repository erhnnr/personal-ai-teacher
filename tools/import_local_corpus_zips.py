"""
Knowledge Factory V2 — Phase 5E Local Official ZIP Corpus Importer

Purpose:
- Scan official course ZIP packages placed in the project root.
- Ignore Knowledge Factory development ZIPs.
- Detect duplicate ZIPs by SHA-256.
- Classify known TYT/AYT/YDT course packages.
- Validate that a package contains basic-html/pageN.html material.
- Extract valid official material into a LOCAL CACHE only.
- Write a machine-readable manifest.

Safety:
- Source ZIPs are never moved, renamed, or deleted.
- Duplicate ZIPs are not extracted twice.
- Unknown ZIPs are reported, not guessed.
- This tool does NOT create claims or mark evidence READY.
- Local cache is runtime/source material and should not be committed.

Default output:
  .local_official_corpus/
  data/knowledge/corpus/local_official_manifest.json
"""

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CACHE_ROOT = (
    PROJECT_ROOT
    / ".local_official_corpus"
)

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "local_official_manifest.json"
)

DEVELOPMENT_ZIP_PREFIXES = (
    "knowledge_factory_",
)

KNOWN_PACKAGES = {
    "tyt-matematik": {
        "package_id": "MEBI-TYT-MATEMATIK",
        "exam": "TYT",
        "subject": "Matematik",
        "scope": "CORE",
    },
    "tyt-turkce": {
        "package_id": "MEBI-TYT-TURKCE",
        "exam": "TYT",
        "subject": "Türkçe",
        "scope": "CORE",
    },
    "tyt-fizik": {
        "package_id": "MEBI-TYT-FIZIK",
        "exam": "TYT",
        "subject": "Fizik",
        "scope": "CORE",
    },
    "tyt-kimya": {
        "package_id": "MEBI-TYT-KIMYA",
        "exam": "TYT",
        "subject": "Kimya",
        "scope": "CORE",
    },
    "tyt-biyoloji": {
        "package_id": "MEBI-TYT-BIYOLOJI",
        "exam": "TYT",
        "subject": "Biyoloji",
        "scope": "CORE",
    },
    "tyt-tarih": {
        "package_id": "MEBI-TYT-TARIH",
        "exam": "TYT",
        "subject": "Tarih",
        "scope": "CORE",
    },
    "tyt-cografya": {
        "package_id": "MEBI-TYT-COGRAFYA",
        "exam": "TYT",
        "subject": "Coğrafya",
        "scope": "CORE",
    },
    "tyt-ayt-felsefe": {
        "package_id": "MEBI-TYT-AYT-FELSEFE",
        "exam": "TYT_AYT",
        "subject": "Felsefe",
        "scope": "CORE",
    },
    "ayt-matematik": {
        "package_id": "MEBI-AYT-MATEMATIK",
        "exam": "AYT",
        "subject": "Matematik",
        "scope": "CORE",
    },
    "ayt-fizik": {
        "package_id": "MEBI-AYT-FIZIK",
        "exam": "AYT",
        "subject": "Fizik",
        "scope": "CORE",
    },
    "ayt-kimya": {
        "package_id": "MEBI-AYT-KIMYA",
        "exam": "AYT",
        "subject": "Kimya",
        "scope": "CORE",
    },
    "ayt-biyoloji": {
        "package_id": "MEBI-AYT-BIYOLOJI",
        "exam": "AYT",
        "subject": "Biyoloji",
        "scope": "CORE",
    },
    "ayt-tarih": {
        "package_id": "MEBI-AYT-TARIH",
        "exam": "AYT",
        "subject": "Tarih",
        "scope": "AUXILIARY",
    },
    "ayt-cografya": {
        "package_id": "MEBI-AYT-COGRAFYA",
        "exam": "AYT",
        "subject": "Coğrafya",
        "scope": "AUXILIARY",
    },
    "ayt-tde": {
        "package_id": "MEBI-AYT-TDE",
        "exam": "AYT",
        "subject": "Türk Dili ve Edebiyatı",
        "scope": "AUXILIARY",
    },
    "ayt-mantik": {
        "package_id": "MEBI-AYT-MANTIK",
        "exam": "AYT",
        "subject": "Mantık",
        "scope": "AUXILIARY",
    },
    "ayt-psikoloji": {
        "package_id": "MEBI-AYT-PSIKOLOJI",
        "exam": "AYT",
        "subject": "Psikoloji",
        "scope": "AUXILIARY",
    },
    "ayt-sosyoloji": {
        "package_id": "MEBI-AYT-SOSYOLOJI",
        "exam": "AYT",
        "subject": "Sosyoloji",
        "scope": "AUXILIARY",
    },
    "ydt-ingilizce": {
        "package_id": "MEBI-YDT-INGILIZCE",
        "exam": "YDT",
        "subject": "İngilizce",
        "scope": "AUXILIARY",
    },
}


def normalize_filename_stem(path):
    stem = Path(path).stem.casefold().strip()

    # Windows duplicate naming: "name (1).zip", "name (2).zip", ...
    stem = re.sub(
        r"\s+\(\d+\)$",
        "",
        stem,
    )

    return stem


def sha256_file(path):
    digest = hashlib.sha256()

    with open(
        path,
        "rb",
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def is_development_zip(path):
    name = Path(path).name.casefold()

    return any(
        name.startswith(
            prefix
        )
        for prefix in DEVELOPMENT_ZIP_PREFIXES
    )


def classify_zip(path):
    stem = normalize_filename_stem(
        path
    )

    metadata = KNOWN_PACKAGES.get(
        stem
    )

    if metadata is None:
        return None

    return dict(
        metadata
    )


def page_number_from_member(name):
    match = re.search(
        r"(?:^|/)page(\d+)\.html$",
        name,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return int(
        match.group(
            1
        )
    )


def inspect_zip(path):
    with zipfile.ZipFile(
        path,
        "r",
    ) as archive:
        members = [
            item.filename
            for item in archive.infolist()
            if not item.is_dir()
        ]

    page_members = []

    for member in members:
        page_number = page_number_from_member(
            member
        )

        if page_number is None:
            continue

        if "basic-html" not in member.casefold():
            continue

        page_members.append(
            (
                page_number,
                member,
            )
        )

    page_members.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    page_numbers = sorted(
        {
            number
            for number, member in page_members
        }
    )

    return {
        "member_count": len(
            members
        ),
        "page_count": len(
            page_numbers
        ),
        "min_page": (
            min(
                page_numbers
            )
            if page_numbers
            else None
        ),
        "max_page": (
            max(
                page_numbers
            )
            if page_numbers
            else None
        ),
        "page_members": [
            {
                "page": number,
                "member": member,
            }
            for number, member in page_members
        ],
    }


def safe_extract_selected(
    zip_path,
    destination,
    page_members,
):
    destination = Path(
        destination
    )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:
        for item in page_members:
            member = item[
                "member"
            ]

            relative = Path(
                member
            )

            if (
                relative.is_absolute()
                or ".." in relative.parts
            ):
                raise ValueError(
                    f"Unsafe ZIP member: {member}"
                )

            target = (
                destination
                / relative
            )

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with archive.open(
                member,
                "r",
            ) as source, open(
                target,
                "wb",
            ) as output:
                shutil.copyfileobj(
                    source,
                    output,
                )


def build_manifest(
    root,
    cache_root,
    extract=True,
):
    root = Path(
        root
    )

    cache_root = Path(
        cache_root
    )

    candidates = sorted(
        root.glob(
            "*.zip"
        ),
        key=lambda path: path.name.casefold(),
    )

    packages = []
    ignored = []
    unknown = []
    duplicates = []

    seen_hashes = {}

    for path in candidates:
        if is_development_zip(
            path
        ):
            ignored.append(
                {
                    "name": path.name,
                    "reason": "DEVELOPMENT_ZIP",
                }
            )
            continue

        classification = classify_zip(
            path
        )

        if classification is None:
            unknown.append(
                {
                    "name": path.name,
                    "reason": "UNKNOWN_PACKAGE_NAME",
                }
            )
            continue

        digest = sha256_file(
            path
        )

        if digest in seen_hashes:
            duplicates.append(
                {
                    "name": path.name,
                    "duplicate_of": seen_hashes[
                        digest
                    ],
                    "sha256": digest,
                }
            )
            continue

        seen_hashes[
            digest
        ] = path.name

        try:
            inspection = inspect_zip(
                path
            )
        except zipfile.BadZipFile:
            packages.append(
                {
                    **classification,
                    "source_zip": path.name,
                    "sha256": digest,
                    "status": "INVALID_ZIP",
                    "page_count": 0,
                }
            )
            continue

        if inspection[
            "page_count"
        ] == 0:
            packages.append(
                {
                    **classification,
                    "source_zip": path.name,
                    "sha256": digest,
                    "status": "NO_BASIC_HTML_PAGES",
                    "page_count": 0,
                }
            )
            continue

        destination = (
            cache_root
            / classification[
                "package_id"
            ]
        )

        if extract:
            safe_extract_selected(
                path,
                destination,
                inspection[
                    "page_members"
                ],
            )

        packages.append(
            {
                **classification,
                "source_zip": path.name,
                "sha256": digest,
                "status": (
                    "IMPORTED"
                    if extract
                    else "VALIDATED"
                ),
                "page_count": inspection[
                    "page_count"
                ],
                "min_page": inspection[
                    "min_page"
                ],
                "max_page": inspection[
                    "max_page"
                ],
                "cache_path": str(
                    destination.relative_to(
                        PROJECT_ROOT
                    )
                )
                if destination.is_relative_to(
                    PROJECT_ROOT
                )
                else str(
                    destination
                ),
            }
        )

    imported = sum(
        1
        for item in packages
        if item["status"] == "IMPORTED"
    )

    core_imported = sum(
        1
        for item in packages
        if (
            item["status"] == "IMPORTED"
            and item["scope"] == "CORE"
        )
    )

    total_pages = sum(
        item.get(
            "page_count",
            0,
        )
        for item in packages
        if item[
            "status"
        ] in {
            "IMPORTED",
            "VALIDATED",
        }
    )

    return {
        "version": "1.0",
        "kind": "LOCAL_OFFICIAL_CORPUS_MANIFEST",
        "source_root": str(
            root
        ),
        "cache_root": str(
            cache_root
        ),
        "package_count": len(
            packages
        ),
        "imported_count": imported,
        "core_imported_count": core_imported,
        "duplicate_count": len(
            duplicates
        ),
        "ignored_count": len(
            ignored
        ),
        "unknown_count": len(
            unknown
        ),
        "total_pages": total_pages,
        "packages": packages,
        "duplicates": duplicates,
        "ignored": ignored,
        "unknown": unknown,
    }


def write_json(
    path,
    data,
):
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


def print_summary(
    manifest,
):
    print("=" * 72)
    print(
        "KNOWLEDGE FACTORY V2 — PHASE 5E LOCAL OFFICIAL ZIP IMPORTER"
    )
    print("=" * 72)

    print(
        f"Packages       : {manifest['package_count']}"
    )

    print(
        f"Imported       : {manifest['imported_count']}"
    )

    print(
        f"Core imported  : {manifest['core_imported_count']}"
    )

    print(
        f"Duplicates     : {manifest['duplicate_count']}"
    )

    print(
        f"Ignored        : {manifest['ignored_count']}"
    )

    print(
        f"Unknown        : {manifest['unknown_count']}"
    )

    print(
        f"Total pages    : {manifest['total_pages']}"
    )

    for package in manifest[
        "packages"
    ]:
        print(
            f"  {package['status']:<18} | "
            f"{package['package_id']:<24} | "
            f"{package.get('page_count', 0)} pages"
        )

    for duplicate in manifest[
        "duplicates"
    ]:
        print(
            "  DUPLICATE          | "
            f"{duplicate['name']} -> "
            f"{duplicate['duplicate_of']}"
        )

    for unknown in manifest[
        "unknown"
    ]:
        print(
            "  UNKNOWN            | "
            f"{unknown['name']}"
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        default=str(
            PROJECT_ROOT
        ),
    )

    parser.add_argument(
        "--cache",
        default=str(
            DEFAULT_CACHE_ROOT
        ),
    )

    parser.add_argument(
        "--manifest",
        default=str(
            DEFAULT_MANIFEST_PATH
        ),
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
    )

    args = parser.parse_args()

    manifest = build_manifest(
        args.root,
        args.cache,
        extract=not args.validate_only,
    )

    write_json(
        args.manifest,
        manifest,
    )

    print_summary(
        manifest
    )

    print(
        f"MANIFEST       | {args.manifest}"
    )

    if any(
        item["status"]
        not in {
            "IMPORTED",
            "VALIDATED",
        }
        for item in manifest[
            "packages"
        ]
    ):
        raise SystemExit(
            2
        )


if __name__ == "__main__":
    main()
