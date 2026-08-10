"""
Knowledge Factory V2 — Phase 5E local ZIP importer tests.
"""

import hashlib
import sys
import zipfile
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

import import_local_corpus_zips as importer


def make_zip(
    path,
    pages,
):
    with zipfile.ZipFile(
        path,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        for page in pages:
            archive.writestr(
                (
                    "book/files/basic-html/"
                    f"page{page}.html"
                ),
                (
                    "<html><body>"
                    f"page {page}"
                    "</body></html>"
                ),
            )


def test_duplicate_windows_name_normalizes():
    assert (
        importer.normalize_filename_stem(
            "tyt-ayt-felsefe (1).zip"
        )
        == "tyt-ayt-felsefe"
    )


def test_development_zip_is_ignored():
    assert importer.is_development_zip(
        "knowledge_factory_v2_phase5d.zip"
    )


def test_known_package_is_classified():
    result = importer.classify_zip(
        "ayt-matematik.zip"
    )

    assert result[
        "package_id"
    ] == "MEBI-AYT-MATEMATIK"

    assert result[
        "scope"
    ] == "CORE"


def test_zip_page_inspection(tmp_path):
    path = (
        tmp_path
        / "tyt-matematik.zip"
    )

    make_zip(
        path,
        [
            1,
            2,
            3,
        ],
    )

    result = importer.inspect_zip(
        path
    )

    assert result[
        "page_count"
    ] == 3

    assert result[
        "min_page"
    ] == 1

    assert result[
        "max_page"
    ] == 3


def test_manifest_detects_duplicate_by_hash(
    tmp_path,
):
    first = (
        tmp_path
        / "tyt-ayt-felsefe.zip"
    )

    second = (
        tmp_path
        / "tyt-ayt-felsefe (1).zip"
    )

    make_zip(
        first,
        [
            1,
            2,
        ],
    )

    second.write_bytes(
        first.read_bytes()
    )

    manifest = importer.build_manifest(
        tmp_path,
        tmp_path / "cache",
        extract=False,
    )

    assert manifest[
        "package_count"
    ] == 1

    assert manifest[
        "duplicate_count"
    ] == 1


def test_import_extracts_only_basic_html_pages(
    tmp_path,
):
    path = (
        tmp_path
        / "tyt-fizik.zip"
    )

    with zipfile.ZipFile(
        path,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "book/files/basic-html/page1.html",
            "<html>physics</html>",
        )
        archive.writestr(
            "book/assets/image.png",
            b"not extracted",
        )

    cache = (
        tmp_path
        / "cache"
    )

    manifest = importer.build_manifest(
        tmp_path,
        cache,
        extract=True,
    )

    package = manifest[
        "packages"
    ][0]

    assert package[
        "status"
    ] == "IMPORTED"

    html_files = list(
        cache.rglob(
            "*.html"
        )
    )

    png_files = list(
        cache.rglob(
            "*.png"
        )
    )

    assert len(
        html_files
    ) == 1

    assert png_files == []
