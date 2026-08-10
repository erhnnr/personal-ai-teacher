"""
KNOWLEDGE FACTORY V2 — PHASE 6D
Deterministic Biology Curriculum -> Official Corpus Crosswalk

Important:
- This tool creates SOURCE CANDIDATES only.
- It does NOT mark evidence READY.
- It uses the canonical Biology curriculum registry as SSOT.
- It only searches official Biology page bundles.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CURRICULUM = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "curriculum_registry"
    / "biology_9_12.json"
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
    / "curriculum_crosswalk"
    / "biology_curriculum_corpus_crosswalk.json"
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
    "ve", "veya", "ile", "ilgili", "icin", "için", "bir", "bu", "su", "şu",
    "olarak", "olan", "hakkinda", "hakkında", "gibi", "ilgili", "yapabilme",
    "sorgulayabilme", "aciklayabilme", "açıklayabilme", "yorumlayabilme",
    "cikarim", "çıkarım", "bilimsel", "elde", "etme", "eder", "edebilme",
    "yurutebilme", "yürütebilme", "toplayabilme", "olusturabilme",
    "oluşturabilme", "analiz", "degerlendirebilme", "değerlendirebilme",
    "canli", "canlı", "canlilar", "canlılar", "biyoloji",
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


def get_grade_records(registry):
    records = registry.get("grade_records")
    if isinstance(records, list):
        return records

    grades = registry.get("grades")
    if isinstance(grades, list) and grades and isinstance(grades[0], dict):
        return grades

    raise ValueError("Canonical curriculum grade_records not found.")


def iter_curriculum_outcomes(registry):
    for grade_record in get_grade_records(registry):
        grade = int(grade_record["grade"])

        for theme in grade_record.get("themes", []):
            theme_number = int(theme["theme_number"])
            theme_name = theme.get("theme_name", "")
            framework = theme.get("content_framework", "")

            for outcome in theme.get("learning_outcomes", []):
                yield {
                    "id": outcome["id"],
                    "grade": grade,
                    "theme_number": theme_number,
                    "theme_name": theme_name,
                    "theme_content_framework": framework,
                    "title": outcome.get("title", ""),
                    "source_page": outcome.get("source_page"),
                }


def get_packages(corpus):
    packages = corpus.get("packages")
    if isinstance(packages, list):
        return packages

    data = corpus.get("package_records")
    if isinstance(data, list):
        return data

    raise ValueError("Corpus package list not found.")


def get_page_text(page):
    for key in ("text", "page_text", "extracted_text", "content"):
        value = page.get(key)
        if isinstance(value, str):
            return value
    return ""


def iter_biology_pages(corpus):
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

            yield {
                "package_id": package_id,
                "page": int(page_number),
                "text": get_page_text(page),
                "text_status": page.get("text_status"),
                "image_status": page.get("image_status"),
                "html_path": page.get("html_path"),
                "image_path": page.get("image_path"),
                "source_anchor": page.get("source_anchor"),
            }


def build_page_index(pages):
    docs = []
    df = Counter()

    for page in pages:
        page_tokens = tokens(page["text"])
        token_set = set(page_tokens)
        docs.append(
            {
                **page,
                "_tokens": page_tokens,
                "_token_set": token_set,
            }
        )
        for token in token_set:
            df[token] += 1

    return docs, df


def query_terms(outcome):
    title_tokens = tokens(outcome["title"])
    theme_tokens = tokens(outcome["theme_name"])
    framework_tokens = tokens(outcome["theme_content_framework"])

    # Preserve order while deduplicating.
    merged = []
    seen = set()
    for token in title_tokens + theme_tokens + framework_tokens:
        if token not in seen:
            merged.append(token)
            seen.add(token)

    return {
        "title": title_tokens,
        "theme": theme_tokens,
        "framework": framework_tokens,
        "all": merged,
    }


def score_page(outcome, page, df, document_count):
    q = query_terms(outcome)
    page_tokens = page["_tokens"]
    page_set = page["_token_set"]

    if not page_tokens:
        return 0.0, {
            "title_hits": [],
            "theme_hits": [],
            "framework_hits": [],
            "title_bigrams": [],
            "package_affinity": False,
        }

    page_counts = Counter(page_tokens)

    def weighted_hits(query_tokens, multiplier):
        score = 0.0
        hits = []
        for token in dict.fromkeys(query_tokens):
            if token not in page_set:
                continue
            hits.append(token)
            idf = math.log(
                (document_count + 1) / (df.get(token, 0) + 1)
            ) + 1.0
            tf = min(page_counts[token], 3)
            score += multiplier * idf * (1.0 + 0.15 * (tf - 1))
        return score, hits

    title_score, title_hits = weighted_hits(q["title"], 8.0)
    theme_score, theme_hits = weighted_hits(q["theme"], 0.5)
    framework_score, framework_hits = weighted_hits(q["framework"], 0.15)

    if not title_hits:
        return 0.0, {
            "title_hits": [],
            "theme_hits": theme_hits,
            "framework_hits": framework_hits[:20],
            "title_bigrams": [],
            "package_affinity": False,
        }

    page_bigrams = set(zip(page_tokens, page_tokens[1:]))
    query_title = list(dict.fromkeys(q["title"]))
    title_bigrams = [
        (a, b)
        for a, b in zip(query_title, query_title[1:])
        if (a, b) in page_bigrams
    ]

    preferred_package = GRADE_PACKAGE_AFFINITY.get(outcome["grade"])
    package_affinity = page["package_id"] == preferred_package

    score = (
        title_score
        + 12.0 * len(title_bigrams)
        + theme_score
        + framework_score
    )

    if package_affinity:
        score *= 1.20
    else:
        score *= 0.82

    if len(title_hits) == 1 and not title_bigrams:
        score *= 0.55

    score *= 1.0 + min(len(title_hits), 5) * 0.08

    return round(score, 6), {
        "title_hits": title_hits,
        "theme_hits": theme_hits,
        "framework_hits": framework_hits[:20],
        "title_bigrams": [" ".join(pair) for pair in title_bigrams],
        "package_affinity": package_affinity,
    }


def rank_candidates(outcome, page_index, df, top_k=8):
    ranked = []

    for page in page_index:
        score, hits = score_page(
            outcome,
            page,
            df,
            len(page_index),
        )
        if score <= 0:
            continue

        ranked.append(
            {
                "package_id": page["package_id"],
                "page": page["page"],
                "score": score,
                "title_hits": hits["title_hits"],
                "theme_hits": hits["theme_hits"],
                "framework_hits": hits["framework_hits"],
                "title_bigrams": hits["title_bigrams"],
                "package_affinity": hits["package_affinity"],
                "source_anchor": page.get("source_anchor"),
                "html_path": page.get("html_path"),
                "image_path": page.get("image_path"),
            }
        )

    ranked.sort(
        key=lambda x: (
            -x["score"],
            x["package_id"],
            x["page"],
        )
    )
    return ranked[:top_k]


def classify_candidate_set(candidates):
    if not candidates:
        return "UNRESOLVED"

    top = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None

    title_hits = len(top["title_hits"])
    bigrams = len(top.get("title_bigrams", []))
    margin = (
        top["score"] - second["score"]
        if second
        else top["score"]
    )

    if (
        title_hits >= 2
        and (bigrams >= 1 or title_hits >= 3)
        and margin >= 2.0
        and top.get("package_affinity") is True
    ):
        return "STRONG_CANDIDATE"

    if title_hits >= 1:
        return "REVIEW_REQUIRED"

    return "WEAK_CANDIDATE"


def build_crosswalk(registry, corpus, top_k=8):
    pages = list(iter_biology_pages(corpus))
    page_index, df = build_page_index(pages)

    outcomes = []
    status_counts = Counter()

    for outcome in iter_curriculum_outcomes(registry):
        candidates = rank_candidates(
            outcome,
            page_index,
            df,
            top_k=top_k,
        )
        status = classify_candidate_set(candidates)
        status_counts[status] += 1

        outcomes.append(
            {
                **outcome,
                "mapping_status": status,
                "evidence_status": "NOT_READY",
                "candidate_pages": candidates,
            }
        )

    return {
        "version": "1.0",
        "kind": "curriculum_corpus_crosswalk",
        "subject": "Biyoloji",
        "authority": "MEB_CURRICULUM_SSOT_PLUS_OFFICIAL_MEBI_CORPUS",
        "mapping_semantics": "SOURCE_CANDIDATES_ONLY",
        "evidence_policy": (
            "Candidate mapping is not evidence verification and must not "
            "set EVIDENCE_READY automatically."
        ),
        "curriculum_outcome_count": len(outcomes),
        "biology_corpus_page_count": len(pages),
        "status_counts": dict(sorted(status_counts.items())),
        "outcomes": outcomes,
    }


def validate_crosswalk(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    if payload.get("curriculum_outcome_count") != 78:
        errors.append(
            "expected 78 Biology curriculum learning outcomes"
        )

    if payload.get("biology_corpus_page_count") != 414:
        errors.append(
            "expected 414 Biology corpus pages "
            "(TYT 172 + AYT 242)"
        )

    outcomes = payload.get("outcomes", [])
    ids = [item.get("id") for item in outcomes]

    if len(ids) != len(set(ids)):
        errors.append("duplicate learning outcome ids")

    for item in outcomes:
        if item.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{item.get('id')}: evidence_status must remain NOT_READY"
            )

        for candidate in item.get("candidate_pages", []):
            if candidate.get("package_id") not in BIOLOGY_PACKAGES:
                errors.append(
                    f"{item.get('id')}: non-Biology package candidate"
                )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--curriculum",
        type=Path,
        default=DEFAULT_CURRICULUM,
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
        "--top-k",
        type=int,
        default=8,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    registry = load_json(args.curriculum)
    corpus = load_json(args.corpus)

    crosswalk = build_crosswalk(
        registry,
        corpus,
        top_k=args.top_k,
    )

    errors = validate_crosswalk(crosswalk)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6D CURRICULUM-CORPUS CROSSWALK")
    print("=" * 72)
    print(
        f"Curriculum outcomes : "
        f"{crosswalk['curriculum_outcome_count']}"
    )
    print(
        f"Biology corpus pages: "
        f"{crosswalk['biology_corpus_page_count']}"
    )

    for status, count in crosswalk["status_counts"].items():
        print(f"{status:<20}: {count}")

    if errors:
        print("CROSSWALK VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, crosswalk)

    print("CROSSWALK VALIDATION: PASS")
    print(f"OUTPUT             | {args.output}")


if __name__ == "__main__":
    main()
