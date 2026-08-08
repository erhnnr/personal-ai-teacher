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