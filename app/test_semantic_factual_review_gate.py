import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import review_source_backed_evidence as gate


def record(
    *,
    grade=12,
    package_id="MEBI-AYT-BIYOLOJI",
    title="DNA replikasyonu genetik bilginin kopyalanması",
    text=None,
):
    if text is None:
        text = (
            "DNA replikasyonu sırasında genetik bilginin kopyalanması "
            "gerçekleşir. DNA molekülü yeni DNA zincirlerinin oluşumunda "
            "kalıp görevi görür. Genetik bilgi hücre bölünmesi öncesinde "
            "korunarak yeni hücrelere aktarılır."
        )

    return {
        "record_id": "BİY.12.2.2::MEBI-AYT-BIYOLOJI::p170",
        "outcome_id": "BİY.12.2.2",
        "grade": grade,
        "theme_number": 2,
        "theme_name": "Gen",
        "outcome_title": title,
        "source": {
            "authority": "MEB",
            "corpus_family": "MEBI_OFFICIAL_LOCAL_CORPUS",
            "package_id": package_id,
            "page": 170,
            "source_anchor": "index.html#p=170",
            "html_path": "files/basic-html/page170.html",
            "image_path": "files/thumb/170.jpg",
            "text_sha256": gate.sha256_text(text),
        },
        "verification": {
            "status": "VERIFIED_SUPPORT_CANDIDATE",
            "checks": {
                "candidate_page_exists": True,
                "official_biology_package": True,
                "text_ready": True,
                "source_anchor_present": True,
                "html_path_present": True,
                "image_path_present": True,
                "package_affinity": True,
            },
        },
        "evidence_text": text,
        "review_status": "REVIEW_PENDING",
        "evidence_status": "NOT_READY",
        "student_visible": False,
        "compiler_policy": "VERBATIM_OFFICIAL_PAGE_TEXT",
    }


def test_good_record_becomes_review_pass_candidate():
    result = gate.review_record(record())
    assert result["review_gate_status"] == "REVIEW_PASS_CANDIDATE"
    assert result["evidence_status"] == "NOT_READY"
    assert result["student_visible"] is False
    assert result["independent_factual_review_required"] is True


def test_wrong_package_affinity_requires_manual_review():
    result = gate.review_record(
        record(
            grade=9,
            package_id="MEBI-AYT-BIYOLOJI",
        )
    )
    assert result["review_gate_status"] == "MANUAL_REVIEW_REQUIRED"


def test_hash_mismatch_requires_manual_review():
    item = record()
    item["source"]["text_sha256"] = "0" * 64
    result = gate.review_record(item)
    assert result["gate_checks"]["hash_matches"] is False
    assert result["review_gate_status"] == "MANUAL_REVIEW_REQUIRED"


def test_short_text_requires_manual_review():
    item = record(text="DNA replikasyonu genetik bilgi")
    result = gate.review_record(item)
    assert result["gate_checks"]["text_length_ok"] is False
    assert result["review_gate_status"] == "MANUAL_REVIEW_REQUIRED"


def test_weak_title_coverage_requires_manual_review():
    item = record(
        title="DNA replikasyonu genetik danışmanlık biyoteknoloji kalıtım",
        text=(
            "DNA replikasyonu hakkında uzun bir resmi kaynak açıklaması "
            "bulunmaktadır. Bu sayfa DNA'nın yapısı ve hücresel süreçler "
            "hakkında çeşitli bilgiler verir ancak diğer outcome terimlerini "
            "doğrudan kapsamaz ve bu metin yeterince uzun tutulmuştur."
        ),
    )
    result = gate.review_record(item)
    assert result["gate_checks"]["title_support_ok"] is False
    assert result["review_gate_status"] == "MANUAL_REVIEW_REQUIRED"


def test_gate_never_marks_evidence_ready():
    payload = gate.build_review_gate(
        {
            "subject": "Biyoloji",
            "records": [record()],
        }
    )
    assert payload["reviews"][0]["evidence_status"] == "NOT_READY"


def test_validation_rejects_student_visible_true():
    payload = gate.build_review_gate(
        {
            "subject": "Biyoloji",
            "records": [record()],
        }
    )
    payload["reviews"][0]["student_visible"] = True
    errors = gate.validate_payload(payload)
    assert errors
