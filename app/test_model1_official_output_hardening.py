import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import teacher


SOURCE_SENTENCE_1 = (
    "Sinir sistemi çevreden ve vücuttan gelen bilgilerin "
    "değerlendirilmesinde görev alır."
)

SOURCE_SENTENCE_2 = (
    "Merkezî sinir sistemi beyin ve omurilikten oluşur."
)


def official_context():
    return json.dumps(
        {
            "source": "MODEL1_OFFICIAL_SOURCE_GROUNDED",
            "subject": "Biyoloji",
            "grade": "11",
            "topic": "Sinir Sistemi",
            "subtopics": [
                "Merkezî sinir sistemi",
            ],
            "sources": [
                {
                    "authority": (
                        "T.C. Millî Eğitim Bakanlığı / MEBİ"
                    ),
                    "page": 42,
                    "excerpt": (
                        SOURCE_SENTENCE_1
                        + "\n"
                        + SOURCE_SENTENCE_2
                        + "\n"
                        + "Bu satır sayfa sonunda yarım kalmış bir açıklama"
                    ),
                }
            ],
        },
        ensure_ascii=False,
    )


class Plan:
    subject = "Biyoloji"
    grade = "11"
    topic = "Sinir Sistemi"
    topics = ["Sinir Sistemi"]


def test_official_context_detector():
    assert teacher._is_model1_official_context(
        official_context()
    ) is True


def test_official_answer_is_extractive_and_drops_truncated_fragments():
    result = (
        teacher._build_model1_official_extractive_answer(
            "Sinir sistemini anlat.",
            official_context(),
        )
    )

    assert SOURCE_SENTENCE_1 in result
    assert SOURCE_SENTENCE_2 in result

    assert (
        "sayfa sonunda yarım kalmış"
        not in result
    )

    assert "kanepe" not in result
    assert "komut oluşturur" not in result


def test_official_ask_teacher_bypasses_local_llm(
    monkeypatch,
):
    monkeypatch.setattr(
        teacher,
        "create_plan",
        lambda question: Plan(),
    )

    monkeypatch.setattr(
        teacher,
        "build_verified_context_for_question",
        lambda plan, question: official_context(),
    )

    def llm_must_not_run(**kwargs):
        raise AssertionError(
            "Official-source MODEL-1 path must not call the LLM."
        )

    monkeypatch.setattr(
        teacher.client.chat.completions,
        "create",
        llm_must_not_run,
    )

    result = teacher.ask_teacher(
        "Sinir sistemini anlat."
    )

    assert SOURCE_SENTENCE_1 in result
    assert SOURCE_SENTENCE_2 in result


def test_official_extractive_mode_does_not_require_lm_connection(
    monkeypatch,
):
    monkeypatch.setattr(
        teacher,
        "create_plan",
        lambda question: Plan(),
    )

    monkeypatch.setattr(
        teacher,
        "build_verified_context_for_question",
        lambda plan, question: official_context(),
    )

    monkeypatch.setattr(
        teacher,
        "check_llm_connection",
        lambda: {
            "connected": False,
            "models": [],
            "error": "offline",
        },
    )

    result = teacher.ask_teacher(
        "Sinir sistemini anlat."
    )

    assert SOURCE_SENTENCE_1 in result
