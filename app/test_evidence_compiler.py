"""
Knowledge Factory V2 — Phase 4 Evidence Compiler tests.
"""

import copy
import json
import sys
from pathlib import Path

import pytest


TOOLS_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "tools"
)

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))

import compile_evidence as compiler


def load_integral_evidence():
    path = (
        Path(__file__)
        .resolve()
        .parent
        .parent
        / "data"
        / "knowledge"
        / "evidence"
        / "matematik"
        / "grade12"
        / "integral"
        / "evidence.json"
    )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def test_integral_compiles_without_llm_paraphrase():
    evidence = load_integral_evidence()

    package = compiler.compile_evidence(
        evidence
    )

    claims = {
        c["id"]: c
        for c in evidence["claims"]
    }

    assert (
        package["concept"]["definitions"][0]["definition"]
        == claims["C2"]["text"]
    )

    assert (
        package["concept"]["rules"][0]
        == claims["C5"]["text"]
    )


def test_every_compiled_fact_has_verbatim_provenance():
    evidence = load_integral_evidence()

    package = compiler.compile_evidence(
        evidence
    )

    assert (
        compiler.validate_factual_draft(
            package,
            evidence,
        )
        is True
    )

    assert all(
        item["copy_mode"] == "VERBATIM"
        for item in package[
            "_provenance"
        ]["items"]
    )


def test_belirli_integral_is_not_in_compiled_concept():
    evidence = load_integral_evidence()

    package = compiler.compile_evidence(
        evidence
    )

    text = json.dumps(
        package["concept"],
        ensure_ascii=False,
    ).casefold()

    assert "belirli integral" not in text


def test_factual_stage_keeps_examples_and_relations_empty():
    evidence = load_integral_evidence()

    package = compiler.compile_evidence(
        evidence
    )

    assert (
        package["examples"]["examples"]
        == []
    )

    assert (
        package["mistakes"]["mistakes"]
        == []
    )

    assert (
        package["relations"]["prerequisites"]
        == []
    )

    assert (
        package["relations"]["next_topics"]
        == []
    )

    assert (
        package["relations"]["related_topics"]
        == []
    )


def test_compiler_rejects_missing_claim_kind():
    evidence = load_integral_evidence()
    evidence = copy.deepcopy(
        evidence
    )

    evidence["claims"][0].pop(
        "kind"
    )

    with pytest.raises(
        ValueError,
        match="no valid compilation kind",
    ):
        compiler.compile_evidence(
            evidence
        )


def test_compiler_detects_any_factual_rewrite():
    evidence = load_integral_evidence()

    package = compiler.compile_evidence(
        evidence
    )

    package["concept"][
        "core_concepts"
    ][0] = (
        package["concept"][
            "core_concepts"
        ][0]
        + " Ek bilgi."
    )

    with pytest.raises(
        ValueError,
        match="not a verbatim evidence copy",
    ):
        compiler.validate_factual_draft(
            package,
            evidence,
        )


def test_definition_claim_requires_term():
    evidence = load_integral_evidence()
    evidence = copy.deepcopy(
        evidence
    )

    for claim in evidence["claims"]:
        if claim["kind"] == "definition":
            claim.pop(
                "term",
                None,
            )
            break

    with pytest.raises(
        ValueError,
        match="requires term",
    ):
        compiler.compile_evidence(
            evidence
        )
