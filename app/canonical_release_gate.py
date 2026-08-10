"""
KNOWLEDGE FACTORY V2 — PHASE 6K
Student Release Gate

Final safety boundary between canonical knowledge packages and the
student-facing teacher.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CANONICAL_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "canonical_ready"
    / "biology"
)

RELEASE_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "student_release"
    / "biology_release_manifest.json"
)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize(text: str) -> str:
    text = str(text or "").strip().casefold()
    text = text.replace("ı", "i")
    text = unicodedata.normalize("NFKD", text)
    return "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )


def _token_variants(token: str):
    """
    Conservative Turkish inflection normalization.

    Example:
    "izini" -> {"izini", "izi"}

    This exists only to prevent false certainty in topic resolution.
    It does not attempt full stemming or semantic expansion.
    """
    variants = {token}

    if len(token) >= 5 and token.endswith(("ni", "nı", "nu", "nü")):
        variants.add(token[:-2])

    return variants


def _tokens(text: str):
    normalized = _normalize(text)
    result = set()

    for token in normalized.replace("-", " ").split():
        if len(token) < 3:
            continue
        result.update(_token_variants(token))

    return result


def canonical_unit_path(unit_id: str) -> Path:
    slug = _normalize(unit_id).replace(" ", "-")
    return CANONICAL_ROOT / slug / "concept.json"


def load_release_manifest():
    if not RELEASE_MANIFEST.exists():
        return None
    return _load_json(RELEASE_MANIFEST)


def validate_canonical_unit(unit):
    errors = []

    if unit.get("verified") is not True:
        errors.append("canonical unit is not verified")

    if unit.get("student_ready") is not False:
        errors.append("canonical source artifact was mutated: student_ready")

    if unit.get("student_visible") is not False:
        errors.append("canonical source artifact was mutated: student_visible")

    grounded = unit.get("source_grounded_content", {})
    text = grounded.get("text", "")
    text_hash = grounded.get("text_sha256")

    if not text:
        errors.append("canonical grounded text missing")

    if _sha256_text(text) != text_hash:
        errors.append("canonical grounded text hash mismatch")

    provenance_hash = unit.get(
        "provenance",
        {},
    ).get("source_text_sha256")

    if text_hash != provenance_hash:
        errors.append("canonical provenance hash mismatch")

    verification = unit.get("verification", {})

    if verification.get("evidence_status") != "READY":
        errors.append("canonical evidence is not READY")

    if (
        verification.get("approval_status")
        != "APPROVED_FOR_EVIDENCE_READY"
    ):
        errors.append("canonical approval is not release eligible")

    for field in (
        "factual_support",
        "outcome_support",
        "source_consistency",
    ):
        if verification.get(field) is not True:
            errors.append(f"canonical verification failed: {field}")

    return errors


def validate_release_entry(entry, unit):
    errors = []

    if entry.get("status") != "RELEASED":
        errors.append("release entry status is not RELEASED")

    if entry.get("student_ready") is not True:
        errors.append("release entry student_ready is not true")

    if entry.get("student_visible") is not True:
        errors.append("release entry student_visible is not true")

    unit_hash = unit.get(
        "source_grounded_content",
        {},
    ).get("text_sha256")

    if entry.get("canonical_text_sha256") != unit_hash:
        errors.append("release hash does not match canonical unit")

    if entry.get("unit_id") != unit.get("id"):
        errors.append("release unit id mismatch")

    return errors


def load_released_unit(unit_id: str):
    manifest = load_release_manifest()
    if not manifest:
        return None

    entries = {
        entry.get("unit_id"): entry
        for entry in manifest.get("units", [])
    }
    entry = entries.get(unit_id)

    if not entry:
        return None

    path = canonical_unit_path(unit_id)
    if not path.exists():
        return None

    unit = _load_json(path)

    if validate_canonical_unit(unit):
        return None

    if validate_release_entry(entry, unit):
        return None

    return unit


def released_units():
    manifest = load_release_manifest()
    if not manifest:
        return []

    result = []

    for entry in manifest.get("units", []):
        unit_id = entry.get("unit_id")
        if not unit_id:
            continue
        unit = load_released_unit(unit_id)
        if unit:
            result.append(unit)

    return result


def match_released_unit(subject, grade, topic):
    """
    Resolve a released canonical unit for an existing planner result.

    Exact normalized topic match wins.
    Otherwise conservative token overlap is allowed only when:
    - subject matches
    - grade matches
    - at least two significant topic tokens overlap
    - there is a unique best match

    Any tie at the best score is blocked.
    """

    subject_n = _normalize(subject)
    grade_n = _normalize(grade)
    topic_n = _normalize(topic)
    topic_tokens = _tokens(topic)

    candidates = []

    for unit in released_units():
        if _normalize(unit.get("subject")) != subject_n:
            continue

        if _normalize(unit.get("grade")) != grade_n:
            continue

        unit_topic = unit.get("topic", "")
        unit_topic_n = _normalize(unit_topic)

        if unit_topic_n == topic_n:
            return unit

        overlap = len(topic_tokens & _tokens(unit_topic))
        if overlap >= 2:
            candidates.append((overlap, unit.get("id"), unit))

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (-item[0], item[1])
    )

    best_score = candidates[0][0]
    best = [
        item
        for item in candidates
        if item[0] == best_score
    ]

    if len(best) != 1:
        return None

    return best[0][2]


def _context_json(unit):
    return json.dumps(
        {
            "source": "KNOWLEDGE_FACTORY_V2_RELEASED_CANONICAL",
            "unit_id": unit["id"],
            "subject": unit["subject"],
            "grade": unit["grade"],
            "topic": unit["topic"],
            "knowledge": {
                "learning_objectives": unit.get(
                    "learning_objectives",
                    [],
                ),
                "source_grounded_content": unit[
                    "source_grounded_content"
                ],
                "provenance": unit["provenance"],
            },
        },
        ensure_ascii=False,
        indent=2,
    )


def build_teacher_context(plan):
    unit = match_released_unit(
        plan.subject,
        plan.grade,
        plan.topic,
    )

    if not unit:
        return None

    return _context_json(unit)


def match_released_unit_from_question(question):
    """
    Resolve a released canonical unit directly from the raw student
    question.

    This is intentionally conservative:
    - exact canonical outcome text contained in the question wins;
    - otherwise at least 4 significant canonical topic tokens and
      >= 60% topic-token coverage are required;
    - ties at the best score are blocked.

    The legacy planner is therefore not allowed to misclassify a
    released canonical Biology outcome as another subject.
    """

    question_n = _normalize(question)
    question_tokens = _tokens(question)
    candidates = []

    for unit in released_units():
        topic = unit.get("topic", "")
        topic_n = _normalize(topic)

        if topic_n and topic_n in question_n:
            candidates.append(
                (
                    10_000,
                    unit.get("id"),
                    unit,
                )
            )
            continue

        topic_tokens = _tokens(topic)
        if not topic_tokens:
            continue

        overlap = len(
            question_tokens & topic_tokens
        )
        coverage = overlap / len(topic_tokens)

        if overlap >= 4 and coverage >= 0.60:
            score = (
                overlap * 100
                + int(coverage * 100)
            )
            candidates.append(
                (
                    score,
                    unit.get("id"),
                    unit,
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (-item[0], item[1])
    )

    best_score = candidates[0][0]
    best = [
        item
        for item in candidates
        if item[0] == best_score
    ]

    if len(best) != 1:
        return None

    return best[0][2]


def build_teacher_context_for_question(
    question,
    plan=None,
):
    """
    Canonical-first release resolution.

    Raw question resolution is authoritative for released canonical
    units. Planner-based resolution remains a conservative secondary
    path for compatibility.
    """

    unit = match_released_unit_from_question(
        question
    )

    if unit:
        return _context_json(unit)

    if plan is None:
        return None

    return build_teacher_context(plan)
