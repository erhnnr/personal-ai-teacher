"""
PHASE 6L — REAL STUDENT E2E RELEASE CHECK

Checks two end-to-end behaviors:

1) At least one released Biology canonical unit can pass through:
   student question -> planner -> canonical release gate -> teacher -> local LLM

2) An unreleased Biology topic is blocked before the local LLM can teach it.

This is a release validation tool, not production runtime code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = PROJECT_ROOT / "app"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from canonical_release_gate import (  # noqa: E402
    build_teacher_context_for_question,
    load_release_manifest,
)
from planner import create_plan  # noqa: E402
from teacher import (  # noqa: E402
    KnowledgeNotReadyError,
    TeacherError,
    ask_teacher,
)
from llm import check_llm_connection  # noqa: E402


def load_released_topics():
    manifest = load_release_manifest()

    if not manifest:
        raise RuntimeError(
            "Student release manifest bulunamadı."
        )

    released = []

    for item in manifest.get("units", []):
        if item.get("status") != "RELEASED":
            continue

        path = PROJECT_ROOT / item["canonical_path"]

        if not path.exists():
            raise RuntimeError(
                f"Canonical dosya bulunamadı: {path}"
            )

        unit = json.loads(
            path.read_text(encoding="utf-8")
        )

        released.append(
            {
                "unit_id": unit["id"],
                "subject": unit["subject"],
                "grade": unit["grade"],
                "topic": unit["topic"],
            }
        )

    return released


def find_student_question_that_resolves(released):
    """
    Try deterministic student-facing phrasings until one released
    canonical unit resolves through the real planner.
    """

    templates = (
        "{topic} konusunu anlat.",
        "Biyoloji {topic} konusunu anlat.",
        "{topic} nedir?",
    )

    attempts = []

    for unit in released:
        for template in templates:
            question = template.format(
                topic=unit["topic"]
            )

            try:
                plan = create_plan(question)
            except Exception as exc:
                attempts.append(
                    {
                        "question": question,
                        "result": f"PLANNER_ERROR: {exc}",
                    }
                )
                continue

            try:
                context = build_teacher_context_for_question(
                    question,
                    plan,
                )
            except Exception as exc:
                attempts.append(
                    {
                        "question": question,
                        "result": f"GATE_ERROR: {exc}",
                    }
                )
                continue

            attempts.append(
                {
                    "question": question,
                    "plan_subject": getattr(
                        plan,
                        "subject",
                        None,
                    ),
                    "plan_grade": getattr(
                        plan,
                        "grade",
                        None,
                    ),
                    "plan_topic": getattr(
                        plan,
                        "topic",
                        None,
                    ),
                    "resolved": bool(context),
                }
            )

            if context:
                return question, plan, context, attempts

    return None, None, None, attempts


def run_released_case():
    released = load_released_topics()

    print(f"Released canonical units : {len(released)}")

    question, plan, context, attempts = (
        find_student_question_that_resolves(
            released
        )
    )

    if not question:
        print("RELEASED E2E: FAIL")
        print(
            "Planner hiçbir released canonical birime "
            "öğrenci sorusundan ulaşamadı."
        )
        print("Resolution attempts:")
        for item in attempts:
            print(json.dumps(
                item,
                ensure_ascii=False,
            ))
        raise SystemExit(1)

    payload = json.loads(context)

    print("Resolved student question:")
    print(f"  {question}")
    print(
        "Planner -> "
        f"{plan.subject} | {plan.grade} | {plan.topic}"
    )
    print(
        "Canonical unit -> "
        f"{payload.get('unit_id')}"
    )

    connection = check_llm_connection()

    if not connection.get("connected"):
        print("RELEASED E2E: BLOCKED_BY_ENVIRONMENT")
        print(
            "LM Studio bağlantısı yok: "
            f"{connection.get('error')}"
        )
        raise SystemExit(2)

    answer = ask_teacher(question)

    if not isinstance(answer, str) or not answer.strip():
        print("RELEASED E2E: FAIL")
        print("Teacher boş yanıt üretti.")
        raise SystemExit(1)

    print("RELEASED E2E: PASS")
    print("Teacher answer preview:")
    preview = answer.strip()
    if len(preview) > 700:
        preview = preview[:700] + "..."
    print(preview)


def run_blocked_case():
    question = "Sinir Sistemi konusunu anlat."

    try:
        answer = ask_teacher(question)
    except KnowledgeNotReadyError as exc:
        print("UNRELEASED E2E: PASS")
        print(
            "Blocked as expected: "
            f"{exc}"
        )
        return
    except TeacherError as exc:
        print("UNRELEASED E2E: FAIL")
        print(
            "Beklenen KnowledgeNotReadyError yerine "
            f"{type(exc).__name__}: {exc}"
        )
        raise SystemExit(1)

    print("UNRELEASED E2E: FAIL")
    print(
        "Release edilmemiş Biyoloji konusu "
        "öğretmen tarafından yanıtlandı."
    )
    print(answer)
    raise SystemExit(1)


def main():
    print("=" * 72)
    print("PHASE 6L — REAL STUDENT E2E RELEASE CHECK")
    print("=" * 72)

    run_released_case()
    print("-" * 72)
    run_blocked_case()

    print("=" * 72)
    print("PHASE 6L E2E RESULT: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
