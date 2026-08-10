"""
KNOWLEDGE FACTORY V2 — PHASE 6G
Semantic/Factual Review Gate (Deterministic Pre-Review)

Purpose:
Apply a stricter, release-oriented review gate to Phase 6F source-backed
evidence records before any record can become an EVIDENCE_READY candidate.

Important safety semantics:
- This tool does NOT perform independent factual verification.
- It does NOT set EVIDENCE_READY.
- It checks source authority, provenance integrity, grade/corpus affinity,
  outcome-specific lexical coverage, and evidence-text integrity.
- Passing records become REVIEW_PASS_CANDIDATE only.
- A later independent semantic/factual approval step is still required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_INPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "evidence_records"
    / "biology_source_backed_evidence.json"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "review_gate"
    / "biology_semantic_factual_review_gate.json"
)

GRADE_PACKAGE_AFFINITY = {
    9: "MEBI-TYT-BIYOLOJI",
    10: "MEBI-TYT-BIYOLOJI",
    11: "MEBI-AYT-BIYOLOJI",
    12: "MEBI-AYT-BIYOLOJI",
}

STOPWORDS = {
    "ve", "veya", "ile", "ilgili", "icin", "bir", "bu", "su", "olarak",
    "olan", "hakkinda", "gibi", "yapabilme", "sorgulayabilme",
    "yorumlayabilme", "aciklayabilme", "olusturabilme", "toplayabilme",
    "degerlendirebilme", "siniflandirabilme", "cozumleyebilme",
    "yurutebilme", "bilimsel", "cikarim", "akil", "deney", "bilgi",
    "model", "canli", "canlilar", "biyoloji", "surec", "surecleri",
    "onemi", "etkileri", "etkileyen", "dayali", "yapilan", "konusunda",
    "uygunlugu",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_text(value: str) -> str:
    value = value or ""
    value = unicodedata.normalize("NFKC", value)
    value = value.casefold()
    value = value.replace("\u0307", "")
    value = value.replace("ı", "i")
    value = re.sub(r"[\u00ad\u200b\u200c\u200d\ufeff]", "", value)
    value = re.sub(r"[^a-z0-9çğıöşü\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def tokens(value: str):
    result = []
    for token in normalize_text(value).split():
        if len(token) < 3:
            continue
        if token in STOPWORDS:
            continue
        result.append(token)
    return list(dict.fromkeys(result))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def review_record(record):
    source = record.get("source", {})
    verification = record.get("verification", {})
    checks = verification.get("checks", {})
    evidence_text = record.get("evidence_text", "")
    outcome_title = record.get("outcome_title", "")
    grade = int(record.get("grade"))

    title_tokens = tokens(outcome_title)
    evidence_tokens = set(tokens(evidence_text))
    matched_tokens = [
        token
        for token in title_tokens
        if token in evidence_tokens
    ]

    coverage_ratio = (
        len(matched_tokens) / len(title_tokens)
        if title_tokens
        else 0.0
    )

    expected_package = GRADE_PACKAGE_AFFINITY.get(grade)
    package_affinity = source.get("package_id") == expected_package

    hash_matches = (
        bool(evidence_text)
        and source.get("text_sha256") == sha256_text(evidence_text)
    )

    provenance_complete = all(
        source.get(key)
        for key in (
            "authority",
            "package_id",
            "page",
            "source_anchor",
            "html_path",
            "image_path",
            "text_sha256",
        )
    )

    authority_ok = source.get("authority") == "MEB"
    compiler_policy_ok = (
        record.get("compiler_policy")
        == "VERBATIM_OFFICIAL_PAGE_TEXT"
    )
    prior_verification_ok = (
        verification.get("status")
        == "VERIFIED_SUPPORT_CANDIDATE"
    )
    prior_checks_ok = all(
        checks.get(key)
        for key in (
            "candidate_page_exists",
            "official_biology_package",
            "text_ready",
            "source_anchor_present",
            "html_path_present",
            "image_path_present",
            "package_affinity",
        )
    )

    text_length_ok = len(evidence_text.strip()) >= 120
    title_support_ok = (
        len(matched_tokens) >= 3
        and coverage_ratio >= 0.50
    )

    gate_checks = {
        "authority_ok": authority_ok,
        "provenance_complete": provenance_complete,
        "hash_matches": hash_matches,
        "package_affinity": package_affinity,
        "compiler_policy_ok": compiler_policy_ok,
        "prior_verification_ok": prior_verification_ok,
        "prior_checks_ok": prior_checks_ok,
        "text_length_ok": text_length_ok,
        "title_support_ok": title_support_ok,
        "matched_title_token_count": len(matched_tokens),
        "title_token_count": len(title_tokens),
        "title_coverage_ratio": round(coverage_ratio, 4),
    }

    hard_pass = all(
        gate_checks[key]
        for key in (
            "authority_ok",
            "provenance_complete",
            "hash_matches",
            "package_affinity",
            "compiler_policy_ok",
            "prior_verification_ok",
            "prior_checks_ok",
            "text_length_ok",
            "title_support_ok",
        )
    )

    if hard_pass:
        status = "REVIEW_PASS_CANDIDATE"
        reason = (
            "official source, complete provenance, intact verbatim text, "
            "correct grade-corpus affinity, and sufficient outcome-specific "
            "coverage"
        )
    else:
        status = "MANUAL_REVIEW_REQUIRED"
        failed = [
            key
            for key, value in gate_checks.items()
            if isinstance(value, bool) and not value
        ]
        reason = "failed deterministic pre-review checks: " + ", ".join(failed)

    return {
        "record_id": record["record_id"],
        "outcome_id": record["outcome_id"],
        "grade": grade,
        "theme_number": record["theme_number"],
        "theme_name": record["theme_name"],
        "outcome_title": outcome_title,
        "review_gate_status": status,
        "reason": reason,
        "matched_title_tokens": matched_tokens,
        "gate_checks": gate_checks,
        "source": source,
        "evidence_status": "NOT_READY",
        "student_visible": False,
        "independent_factual_review_required": True,
    }


def build_review_gate(payload):
    records = payload.get("records", [])
    reviews = []
    counts = Counter()

    for record in records:
        review = review_record(record)
        reviews.append(review)
        counts[review["review_gate_status"]] += 1

    return {
        "version": "1.0",
        "kind": "semantic_factual_review_gate",
        "subject": payload.get("subject"),
        "gate_semantics": (
            "Deterministic pre-review only. REVIEW_PASS_CANDIDATE is not "
            "independent factual verification and is not EVIDENCE_READY."
        ),
        "record_count": len(reviews),
        "status_counts": dict(sorted(counts.items())),
        "reviews": reviews,
    }


def validate_payload(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    reviews = payload.get("reviews", [])

    if payload.get("record_count") != len(reviews):
        errors.append("record_count mismatch")

    ids = [item.get("record_id") for item in reviews]
    if len(ids) != len(set(ids)):
        errors.append("duplicate review record ids")

    for item in reviews:
        if item.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{item.get('record_id')}: evidence_status must remain NOT_READY"
            )

        if item.get("student_visible") is not False:
            errors.append(
                f"{item.get('record_id')}: student_visible must be false"
            )

        if item.get("independent_factual_review_required") is not True:
            errors.append(
                f"{item.get('record_id')}: independent factual review must remain required"
            )

        if item.get("review_gate_status") == "REVIEW_PASS_CANDIDATE":
            checks = item.get("gate_checks", {})
            required = (
                "authority_ok",
                "provenance_complete",
                "hash_matches",
                "package_affinity",
                "compiler_policy_ok",
                "prior_verification_ok",
                "prior_checks_ok",
                "text_length_ok",
                "title_support_ok",
            )
            if not all(checks.get(key) for key in required):
                errors.append(
                    f"{item.get('record_id')}: pass candidate has failed checks"
                )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    source_payload = load_json(args.input)
    payload = build_review_gate(source_payload)
    errors = validate_payload(payload)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6G SEMANTIC/FACTUAL REVIEW GATE")
    print("=" * 72)
    print(f"Input records             : {payload['record_count']}")

    for status, count in payload["status_counts"].items():
        print(f"{status:<26}: {count}")

    if errors:
        print("REVIEW GATE VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, payload)

    print("REVIEW GATE VALIDATION: PASS")
    print("Evidence status           : NOT_READY")
    print("Student visible           : False")
    print("Independent factual review: REQUIRED")
    print(f"OUTPUT                    | {args.output}")


if __name__ == "__main__":
    main()
