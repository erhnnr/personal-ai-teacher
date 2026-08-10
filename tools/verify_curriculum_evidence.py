"""
KNOWLEDGE FACTORY V2 — PHASE 6E
Deterministic Curriculum Evidence Verification

Purpose:
Verify whether curriculum-crosswalk source candidates have sufficient
outcome-specific support and complete provenance to proceed to semantic
evidence review.

Safety:
- This tool NEVER sets EVIDENCE_READY.
- A deterministic PASS means "verified support candidate", not factual truth.
- Semantic/factual evidence approval remains a later gate.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CROSSWALK = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "curriculum_crosswalk"
    / "biology_curriculum_corpus_crosswalk.json"
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
    / "evidence_verification"
    / "biology_evidence_verification.json"
)

BIOLOGY_PACKAGES = {
    "MEBI-TYT-BIYOLOJI",
    "MEBI-AYT-BIYOLOJI",
}

GRADE_PACKAGE_AFFINITY = {
    9: "MEBI-TYT-BIYOLOJI",
    10: "MEBI-TYT-BIYOLOJI",
    11: "MEBI-AYT-BIYOLOJI",
    12: "MEBI-AYT-BIYOLOJI",
}

STOPWORDS = {
    "ve", "veya", "ile", "ilgili", "icin", "bir", "bu", "su",
    "olarak", "olan", "hakkinda", "gibi", "yapabilme",
    "sorgulayabilme", "yorumlayabilme", "aciklayabilme",
    "olusturabilme", "toplayabilme", "degerlendirebilme",
    "siniflandirabilme", "cozumleyebilme", "yurutebilme",
    "bilimsel", "cikarim", "akil", "deney", "bilgi", "model",
    "canli", "canlilar", "biyoloji", "hakkinda", "surec",
    "surecleri", "onemi", "etkileri", "etkileyen", "dayali",
    "yapilan", "konusunda", "uygunlugu",
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
    return result


def get_packages(corpus):
    packages = corpus.get("packages")
    if isinstance(packages, list):
        return packages

    packages = corpus.get("package_records")
    if isinstance(packages, list):
        return packages

    raise ValueError("Corpus package list not found.")


def page_text(page):
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
                "text": page_text(page),
                "text_status": page.get("text_status"),
                "image_status": page.get("image_status"),
                "source_anchor": page.get("source_anchor"),
                "html_path": page.get("html_path"),
                "image_path": page.get("image_path"),
            }

    return lookup


def distinctive_title_tokens(title: str):
    return list(dict.fromkeys(tokens(title)))


def title_bigrams(title_tokens):
    return list(zip(title_tokens, title_tokens[1:]))


def verify_candidate(outcome, candidate, page_lookup):
    key = (
        candidate.get("package_id"),
        candidate.get("page"),
    )
    page = page_lookup.get(key)

    checks = {
        "candidate_page_exists": page is not None,
        "official_biology_package": (
            candidate.get("package_id") in BIOLOGY_PACKAGES
        ),
        "text_ready": False,
        "source_anchor_present": False,
        "html_path_present": False,
        "image_path_present": False,
        "package_affinity": False,
        "distinctive_title_hit_count": 0,
        "title_bigram_hit_count": 0,
    }

    if page is None:
        return {
            "verification_status": "REJECTED",
            "reason": "candidate page not found in official local corpus",
            "checks": checks,
            "matched_title_tokens": [],
            "matched_title_bigrams": [],
        }

    text = page["text"]
    normalized = normalize_text(text)
    page_tokens = normalized.split()
    page_token_set = set(page_tokens)
    page_bigrams = set(zip(page_tokens, page_tokens[1:]))

    title_tokens = distinctive_title_tokens(outcome.get("title", ""))
    matched_title_tokens = [
        token
        for token in title_tokens
        if token in page_token_set
    ]

    matched_title_bigrams = [
        " ".join(pair)
        for pair in title_bigrams(title_tokens)
        if pair in page_bigrams
    ]

    checks["text_ready"] = bool(text.strip())
    checks["source_anchor_present"] = bool(page.get("source_anchor"))
    checks["html_path_present"] = bool(page.get("html_path"))
    checks["image_path_present"] = bool(page.get("image_path"))
    checks["package_affinity"] = (
        candidate.get("package_id")
        == GRADE_PACKAGE_AFFINITY.get(int(outcome["grade"]))
    )
    checks["distinctive_title_hit_count"] = len(
        matched_title_tokens
    )
    checks["title_bigram_hit_count"] = len(
        matched_title_bigrams
    )

    provenance_complete = (
        checks["candidate_page_exists"]
        and checks["official_biology_package"]
        and checks["text_ready"]
        and checks["source_anchor_present"]
        and checks["html_path_present"]
        and checks["image_path_present"]
    )

    # Conservative deterministic verification:
    # PASS requires specific outcome support plus complete provenance.
    strong_support = (
        len(matched_title_tokens) >= 3
        and checks["package_affinity"] is True
    )

    weak_support = len(matched_title_tokens) >= 1

    if provenance_complete and strong_support:
        status = "VERIFIED_SUPPORT_CANDIDATE"
        reason = (
            "complete provenance, correct grade-corpus affinity, and "
            "at least three distinctive outcome-title token matches"
        )
    elif provenance_complete and weak_support:
        status = "REVIEW_REQUIRED"
        reason = (
            "provenance complete but outcome-specific support is insufficient"
        )
    else:
        status = "REJECTED"
        reason = (
            "missing provenance, missing text, or no distinctive outcome support"
        )

    return {
        "verification_status": status,
        "reason": reason,
        "checks": checks,
        "matched_title_tokens": matched_title_tokens,
        "matched_title_bigrams": matched_title_bigrams,
    }


def verify_outcome(outcome, page_lookup, max_candidates=3):
    candidates = outcome.get("candidate_pages", [])[:max_candidates]
    verified_candidates = []

    for candidate in candidates:
        result = verify_candidate(
            outcome,
            candidate,
            page_lookup,
        )

        verified_candidates.append(
            {
                "package_id": candidate.get("package_id"),
                "page": candidate.get("page"),
                "crosswalk_score": candidate.get("score"),
                "crosswalk_status": outcome.get("mapping_status"),
                **result,
            }
        )

    status_priority = {
        "VERIFIED_SUPPORT_CANDIDATE": 3,
        "REVIEW_REQUIRED": 2,
        "REJECTED": 1,
    }

    verified_candidates.sort(
        key=lambda item: (
            -status_priority[item["verification_status"]],
            -item["checks"]["distinctive_title_hit_count"],
            -item["checks"]["title_bigram_hit_count"],
            -(item.get("crosswalk_score") or 0),
        )
    )

    best = verified_candidates[0] if verified_candidates else None

    if best is None:
        outcome_status = "REJECTED"
    else:
        outcome_status = best["verification_status"]

    return {
        "id": outcome["id"],
        "grade": outcome["grade"],
        "theme_number": outcome["theme_number"],
        "theme_name": outcome["theme_name"],
        "title": outcome["title"],
        "crosswalk_status": outcome.get("mapping_status"),
        "verification_status": outcome_status,
        "evidence_status": "NOT_READY",
        "best_candidate": best,
        "candidate_results": verified_candidates,
    }


def build_verification(crosswalk, corpus, max_candidates=3):
    page_lookup = build_page_lookup(corpus)
    outcomes = []
    counts = Counter()

    for outcome in crosswalk.get("outcomes", []):
        record = verify_outcome(
            outcome,
            page_lookup,
            max_candidates=max_candidates,
        )
        outcomes.append(record)
        counts[record["verification_status"]] += 1

    return {
        "version": "1.0",
        "kind": "curriculum_evidence_verification",
        "subject": "Biyoloji",
        "verification_scope": (
            "DETERMINISTIC_SOURCE_SUPPORT_AND_PROVENANCE"
        ),
        "verification_semantics": (
            "VERIFIED_SUPPORT_CANDIDATE is not EVIDENCE_READY and does "
            "not independently prove factual correctness."
        ),
        "curriculum_outcome_count": len(outcomes),
        "status_counts": dict(sorted(counts.items())),
        "outcomes": outcomes,
    }


def validate_verification(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    if payload.get("curriculum_outcome_count") != 78:
        errors.append("expected 78 Biology outcomes")

    outcomes = payload.get("outcomes", [])
    ids = [item.get("id") for item in outcomes]

    if len(ids) != len(set(ids)):
        errors.append("duplicate outcome ids")

    for item in outcomes:
        if item.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{item.get('id')}: evidence_status must remain NOT_READY"
            )

        best = item.get("best_candidate")
        if (
            item.get("verification_status")
            == "VERIFIED_SUPPORT_CANDIDATE"
        ):
            if not best:
                errors.append(
                    f"{item.get('id')}: verified without best candidate"
                )
                continue

            checks = best.get("checks", {})
            if not all(
                checks.get(key)
                for key in (
                    "candidate_page_exists",
                    "official_biology_package",
                    "text_ready",
                    "source_anchor_present",
                    "html_path_present",
                    "image_path_present",
                )
            ):
                errors.append(
                    f"{item.get('id')}: verified with incomplete provenance"
                )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--crosswalk",
        type=Path,
        default=DEFAULT_CROSSWALK,
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
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=3,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    crosswalk = load_json(args.crosswalk)
    corpus = load_json(args.corpus)

    payload = build_verification(
        crosswalk,
        corpus,
        max_candidates=args.max_candidates,
    )

    errors = validate_verification(payload)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6E EVIDENCE VERIFICATION")
    print("=" * 72)
    print(
        f"Curriculum outcomes : "
        f"{payload['curriculum_outcome_count']}"
    )

    for status, count in payload["status_counts"].items():
        print(f"{status:<28}: {count}")

    if errors:
        print("VERIFICATION VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, payload)

    print("VERIFICATION VALIDATION: PASS")
    print(f"OUTPUT                  | {args.output}")


if __name__ == "__main__":
    main()
