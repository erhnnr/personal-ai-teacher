"""
KNOWLEDGE FACTORY V2 — PHASE 6F
Source-Backed Evidence Record Builder

Purpose:
Convert VERIFIED_SUPPORT_CANDIDATE outcomes from Phase 6E into canonical
source-backed evidence records.

Safety:
- This tool NEVER sets EVIDENCE_READY.
- Records are REVIEW_PENDING until semantic/factual review.
- Page text is copied from the official local corpus without LLM rewriting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_VERIFICATION = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "evidence_verification"
    / "biology_evidence_verification.json"
)

DEFAULT_CORPUS = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "local_page_bundle_index.json"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "evidence_records"
    / "biology_source_backed_evidence.json"
)

BIOLOGY_PACKAGES = {
    "MEBI-TYT-BIYOLOJI",
    "MEBI-AYT-BIYOLOJI",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_packages(corpus):
    packages = corpus.get("packages")
    if isinstance(packages, list):
        return packages

    packages = corpus.get("package_records")
    if isinstance(packages, list):
        return packages

    raise ValueError("Corpus package list not found.")


def extract_page_text(page):
    for key in ("text", "page_text", "extracted_text", "content"):
        value = page.get(key)
        if isinstance(value, str):
            return value
    return ""


def build_page_lookup(corpus):
    lookup = {}

    for package in get_packages(corpus):
        package_id = package.get("package_id") or package.get("id")
        if package_id not in BIOLOGY_PACKAGES:
            continue

        for page in package.get("pages", []):
            page_number = (
                page.get("page")
                if page.get("page") is not None
                else page.get("page_number")
            )

            key = (package_id, int(page_number))

            lookup[key] = {
                "package_id": package_id,
                "page": int(page_number),
                "text": extract_page_text(page),
                "text_status": page.get("text_status"),
                "image_status": page.get("image_status"),
                "source_anchor": page.get("source_anchor"),
                "html_path": page.get("html_path"),
                "image_path": page.get("image_path"),
            }

    return lookup


def text_sha256(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def build_record(outcome, page_lookup):
    if outcome.get("verification_status") != "VERIFIED_SUPPORT_CANDIDATE":
        raise ValueError(
            f"{outcome.get('id')}: outcome is not VERIFIED_SUPPORT_CANDIDATE"
        )

    best = outcome.get("best_candidate")
    if not best:
        raise ValueError(
            f"{outcome.get('id')}: missing best candidate"
        )

    key = (
        best.get("package_id"),
        best.get("page"),
    )

    page = page_lookup.get(key)
    if page is None:
        raise ValueError(
            f"{outcome.get('id')}: best candidate page not found"
        )

    text = page["text"]
    if not text.strip():
        raise ValueError(
            f"{outcome.get('id')}: source page text is empty"
        )

    for field in (
        "source_anchor",
        "html_path",
        "image_path",
    ):
        if not page.get(field):
            raise ValueError(
                f"{outcome.get('id')}: missing provenance field {field}"
            )

    record_id = (
        f"{outcome['id']}::"
        f"{page['package_id']}::"
        f"p{page['page']}"
    )

    return {
        "record_id": record_id,
        "outcome_id": outcome["id"],
        "grade": outcome["grade"],
        "theme_number": outcome["theme_number"],
        "theme_name": outcome["theme_name"],
        "outcome_title": outcome["title"],
        "source": {
            "authority": "MEB",
            "corpus_family": "MEBI_OFFICIAL_LOCAL_CORPUS",
            "package_id": page["package_id"],
            "page": page["page"],
            "source_anchor": page["source_anchor"],
            "html_path": page["html_path"],
            "image_path": page["image_path"],
            "text_sha256": text_sha256(text),
        },
        "verification": {
            "status": "VERIFIED_SUPPORT_CANDIDATE",
            "crosswalk_status": best.get("crosswalk_status"),
            "crosswalk_score": best.get("crosswalk_score"),
            "matched_title_tokens": best.get(
                "matched_title_tokens",
                [],
            ),
            "matched_title_bigrams": best.get(
                "matched_title_bigrams",
                [],
            ),
            "checks": best.get("checks", {}),
        },
        "evidence_text": text,
        "review_status": "REVIEW_PENDING",
        "evidence_status": "NOT_READY",
        "student_visible": False,
        "compiler_policy": "VERBATIM_OFFICIAL_PAGE_TEXT",
    }


def build_records(verification, corpus):
    page_lookup = build_page_lookup(corpus)

    records = []

    for outcome in verification.get("outcomes", []):
        if outcome.get(
            "verification_status"
        ) != "VERIFIED_SUPPORT_CANDIDATE":
            continue

        records.append(
            build_record(
                outcome,
                page_lookup,
            )
        )

    return {
        "version": "1.0",
        "kind": "source_backed_evidence_records",
        "subject": "Biyoloji",
        "authority": "MEB",
        "record_semantics": (
            "Source-backed review candidates only; not EVIDENCE_READY."
        ),
        "record_count": len(records),
        "records": records,
    }


def validate_payload(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    records = payload.get("records", [])

    if payload.get("record_count") != len(records):
        errors.append("record_count mismatch")

    ids = [record.get("record_id") for record in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate record ids")

    for record in records:
        if record.get("review_status") != "REVIEW_PENDING":
            errors.append(
                f"{record.get('record_id')}: review_status must be REVIEW_PENDING"
            )

        if record.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{record.get('record_id')}: evidence_status must be NOT_READY"
            )

        if record.get("student_visible") is not False:
            errors.append(
                f"{record.get('record_id')}: student_visible must be false"
            )

        source = record.get("source", {})
        for key in (
            "authority",
            "package_id",
            "page",
            "source_anchor",
            "html_path",
            "image_path",
            "text_sha256",
        ):
            if not source.get(key):
                errors.append(
                    f"{record.get('record_id')}: missing source field {key}"
                )

        if not record.get("evidence_text", "").strip():
            errors.append(
                f"{record.get('record_id')}: evidence_text is empty"
            )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verification",
        type=Path,
        default=DEFAULT_VERIFICATION,
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    verification = load_json(
        args.verification
    )
    corpus = load_json(
        args.corpus
    )

    payload = build_records(
        verification,
        corpus,
    )

    errors = validate_payload(
        payload
    )

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6F SOURCE-BACKED EVIDENCE RECORDS")
    print("=" * 72)
    print(
        f"Verified support input : "
        f"{payload['record_count']}"
    )

    if errors:
        print("EVIDENCE RECORD VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(
        args.output,
        payload,
    )

    print("EVIDENCE RECORD VALIDATION: PASS")
    print(
        f"Review status          : REVIEW_PENDING"
    )
    print(
        f"Evidence status        : NOT_READY"
    )
    print(
        f"Student visible        : False"
    )
    print(
        f"OUTPUT                 | {args.output}"
    )


if __name__ == "__main__":
    main()
