"""
Knowledge Factory V2 Phase 3.4.2:
generation-boundary regression tests.
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


def response_schema(record):
    return (
        generator
        .build_structured_response_format(
            record
        )["json_schema"]["schema"]
    )


def test_math_structured_output_blocks_llm_examples():
    schema = response_schema(
        {
            "subject": "Matematik",
            "topic": "İntegral",
        }
    )

    examples = (
        schema["properties"]["examples"]
        ["properties"]["examples"]
    )

    assert examples["maxItems"] == 0


def test_structured_output_blocks_llm_relations():
    schema = response_schema(
        {
            "subject": "Matematik",
            "topic": "İntegral",
        }
    )

    relations = (
        schema["properties"]["relations"]
        ["properties"]
    )

    assert (
        relations["prerequisites"]["maxItems"]
        == 0
    )
    assert (
        relations["next_topics"]["maxItems"]
        == 0
    )
    assert (
        relations["related_topics"]["maxItems"]
        == 0
    )


def test_non_math_examples_are_not_globally_disabled():
    schema = response_schema(
        {
            "subject": "Türkçe",
            "topic": "Sözcükte Anlam",
        }
    )

    examples = (
        schema["properties"]["examples"]
        ["properties"]["examples"]
    )

    assert "maxItems" not in examples


def test_empty_math_examples_are_valid_in_factual_pass():
    package = {
        "examples": {
            "topic": "İntegral",
            "examples": [],
        }
    }

    assert (
        generator.validate_generated_math_package(
            package,
            "Matematik",
        )
        is True
    )


def test_prompt_matches_generation_boundaries():
    prompt = generator.build_prompt(
        {
            "exam": "AYT",
            "subject": "Matematik",
            "topic": "İntegral",
        },
        "12",
        evidence={
            "id": "matematik.grade12.integral",
            "claims": [
                {
                    "id": "C1",
                    "text": "Belirsiz integral açıklanır.",
                    "source_refs": [],
                }
            ],
            "sources": [],
            "coverage": {
                "curriculum_objectives": [],
                "excluded_terms": [
                    "belirli integral"
                ],
            },
        },
    )

    assert (
        "examples.examples TAM OLARAK boş dizi []"
        in prompt
    )
    assert (
        "relations.prerequisites, relations.next_topics "
        "ve relations.related_topics bu aşamada TAM OLARAK []"
        in prompt
    )
