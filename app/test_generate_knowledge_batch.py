import json
import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

TOOLS_PATH = (
    PROJECT_ROOT
    / "tools"
)

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS_PATH),
    )


import generate_knowledge_batch


def write_json(
    path,
    data,
):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def create_integral_draft(
    root,
    expected,
):
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_json(
        root / "concept.json",
        {
            "id": "matematik.grade12.integral",
            "subject": "Matematik",
            "grade": "12",
            "topic": "İntegral",
            "learning_objectives": [
                "İntegral kavramını açıklayabilme"
            ],
            "prerequisites": [
                "Türev"
            ],
            "core_concepts": [
                "Belirsiz integral"
            ],
            "definitions": [
                {
                    "term": "İntegral",
                    "definition": (
                        "Bir fonksiyonun "
                        "antitürevleriyle ilişkili "
                        "matematiksel kavramdır."
                    ),
                }
            ],
            "rules": [
                "Belirsiz integralde sabit terim bulunur."
            ],
            "common_confusions": [
                "Sabit terimi unutmak"
            ],
            "teaching_notes": [
                "Önce türev ilişkisi anlatılır."
            ],
        },
    )

    write_json(
        root / "examples.json",
        {
            "topic": "İntegral",
            "examples": [
                {
                    "id": "INT-E1",
                    "level": "basic",
                    "type": "concept",
                    "question": (
                        "f(x) = 3x + 2 fonksiyonunun "
                        "belirli integralini [1,4] "
                        "aralığında bulun."
                    ),
                    "answer": (
                        f"∫[1 to 4] (3x + 2) dx = "
                        f"{expected}"
                    ),
                    "learning_point": (
                        "Belirli integral hesaplamak."
                    ),
                    "validation": {
                        "type": "definite_integral",
                        "expression": "3*x + 2",
                        "variable": "x",
                        "lower": 1,
                        "upper": 4,
                        "expected": expected,
                    },
                }
            ],
        },
    )

    write_json(
        root / "mistakes.json",
        {
            "topic": "İntegral",
            "mistakes": [
                {
                    "id": "INT-M1",
                    "error": (
                        "Sınırları yanlış uygulamak"
                    ),
                    "explanation": (
                        "Üst ve alt sınır doğru "
                        "sırada uygulanmalıdır."
                    ),
                    "teacher_action": (
                        "F(b)-F(a) kuralını tekrar et."
                    ),
                }
            ],
        },
    )

    write_json(
        root / "relations.json",
        {
            "topic": "İntegral",
            "prerequisites": [
                {
                    "topic": "Türev",
                    "reason": (
                        "İntegral ve türev ilişkilidir."
                    ),
                }
            ],
            "next_topics": [],
            "related_topics": [],
        },
    )

    write_json(
        root / "draft_meta.json",
        {
            "status": "DRAFT",
            "verified": False,
            "structure_status": None,
            "factual_review_status": None,
        },
    )


def test_batch_review_accepts_correct_math(
    tmp_path,
):

    create_integral_draft(
        tmp_path,
        "57/2",
    )

    structure, factual = (
        generate_knowledge_batch
        .run_automated_reviews(
            tmp_path,
            "Matematik",
        )
    )

    assert structure == "PASS"
    assert factual == "PASS"

    metadata = json.loads(
        (
            tmp_path
            / "draft_meta.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert metadata["verified"] is False
    assert metadata["structure_status"] == "PASS"
    assert (
        metadata["factual_review_status"]
        == "PASS"
    )


def test_batch_review_rejects_wrong_math(
    tmp_path,
):

    create_integral_draft(
        tmp_path,
        15,
    )

    structure, factual = (
        generate_knowledge_batch
        .run_automated_reviews(
            tmp_path,
            "Matematik",
        )
    )

    assert structure == "PASS"
    assert factual == "FAIL"

    metadata = json.loads(
        (
            tmp_path
            / "draft_meta.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata["factual_review_status"]
        == "FAIL"
    )

    assert metadata["verified"] is False


def test_slugify_handles_turkish_i():

    assert (
        generate_knowledge_batch.slugify(
            "İntegral"
        )
        == "integral"
    )

    assert (
        generate_knowledge_batch.slugify(
            "İtme ve Momentum"
        )
        == "itme_ve_momentum"
    )

    assert (
        generate_knowledge_batch.slugify(
            "İş Enerji ve Güç"
        )
        == "is_enerji_ve_guc"
    )


def test_math_package_without_validation_is_rejected():

    package = {
        "examples": {
            "topic": "Matematik",
            "examples": [
                {
                    "id": "E1",
                    "question": "2 + 2 kaçtır?",
                    "answer": "4",
                    "learning_point": "Toplama",
                }
            ],
        }
    }

    try:
        generate_knowledge_batch.validate_generated_math_package(
            package,
            "Matematik",
        )

        assert False, (
            "Missing validation should have been rejected."
        )

    except ValueError as exc:

        assert (
            "missing validation"
            in str(exc)
        )


def test_math_package_with_unsupported_validation_is_rejected():

    package = {
        "examples": {
            "topic": "Matematik",
            "examples": [
                {
                    "id": "E1",
                    "question": "Bir matematik sorusu.",
                    "answer": "Bir cevap.",
                    "learning_point": "Test",
                    "validation": {
                        "type": "unknown_math_type"
                    },
                }
            ],
        }
    }

    try:
        generate_knowledge_batch.validate_generated_math_package(
            package,
            "Matematik",
        )

        assert False, (
            "Unsupported validation type "
            "should have been rejected."
        )

    except ValueError as exc:

        message = str(exc)

        assert (
            "validation contract failed"
            in message
        )

        assert (
            "unknown_math_type"
            in message
        )

def test_math_package_with_missing_required_field_is_rejected():

    package = {
        "examples": {
            "topic": "Fonksiyonlar",
            "examples": [
                {
                    "id": "E1",
                    "question": "f(2) değerini bulun.",
                    "answer": "8",
                    "learning_point": "Fonksiyon değeri",
                    "validation": {
                        "type": "function_value",
                        "variable": "x",
                        "input": 2,
                        "expected": 8
                    },
                }
            ],
        }
    }

    try:
        generate_knowledge_batch.validate_generated_math_package(
            package,
            "Matematik",
        )

        assert False, (
            "Missing required contract field "
            "should have been rejected."
        )

    except ValueError as exc:

        message = str(exc)

        assert (
            "validation contract failed"
            in message
        )

        assert (
            "'function' is a required property"
            in message
        )
def test_overwrite_removes_stale_draft(
    tmp_path,
):

    draft_path = (
        tmp_path
        / "integral"
    )

    draft_path.mkdir()

    stale_file = (
        draft_path
        / "examples.json"
    )

    stale_file.write_text(
        '{"stale": true}',
        encoding="utf-8",
    )

    removed = (
        generate_knowledge_batch
        .prepare_draft_for_overwrite(
            draft_path,
            True,
        )
    )

    assert removed is True
    assert not draft_path.exists()


def test_no_overwrite_preserves_existing_draft(
    tmp_path,
):

    draft_path = (
        tmp_path
        / "integral"
    )

    draft_path.mkdir()

    stale_file = (
        draft_path
        / "examples.json"
    )

    stale_file.write_text(
        '{"stale": true}',
        encoding="utf-8",
    )

    removed = (
        generate_knowledge_batch
        .prepare_draft_for_overwrite(
            draft_path,
            False,
        )
    )

    assert removed is False
    assert draft_path.exists()
    assert stale_file.exists()        