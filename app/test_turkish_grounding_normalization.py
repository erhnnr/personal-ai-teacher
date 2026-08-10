"""
Knowledge Factory V2 Phase 3.3.2:
Turkish Unicode grounding normalization tests.
"""

import sys
from pathlib import Path


TOOLS_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "tools"
)

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS_PATH),
    )

import generate_knowledge_batch as generator


def test_capital_turkish_i_stays_single_token():
    assert (
        generator.grounding_tokens(
            "İntegral"
        )
        == ["integral"]
    )


def test_turkish_grounding_normalization():
    assert (
        generator.normalize_grounding_text(
            "İntegral, Türev, Çözüm"
        )
        == "integral, turev, cozum"
    )
