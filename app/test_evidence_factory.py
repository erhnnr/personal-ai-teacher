"""
Tests for Knowledge Factory V2 evidence layer.
"""

import sys
from pathlib import Path
import pytest

TOOLS_PATH = Path(__file__).resolve().parent.parent / "tools"

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))

import evidence_factory


def test_slugify_turkish():
    assert evidence_factory.slugify(
        "İnsan ve Çevre"
    ) == "insan_ve_cevre"


def test_registry_rejects_duplicate_ids():
    registry = {
        "sources": [
            {
                "id": "SRC-1",
                "publisher": "MEB",
                "title": "A",
                "url": "https://example.test/a",
            },
            {
                "id": "SRC-1",
                "publisher": "MEB",
                "title": "B",
                "url": "https://example.test/b",
            },
        ]
    }

    with pytest.raises(ValueError, match="Duplicate source id"):
        evidence_factory.validate_registry(registry)


def test_create_empty_package():
    package = evidence_factory.create_empty_package(
        "AYT",
        "Matematik",
        "12",
        "Limit",
    )

    assert package["id"] == "matematik.grade12.limit"
    assert package["status"] == "EVIDENCE_DRAFT"
    assert package["sources"] == []
    assert package["claims"] == []
