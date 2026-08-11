"""
MODEL-1 Official Source Grounding

Purpose:
Provide a bounded student-teaching fallback for curriculum topics that do
not yet have a canonical/human-reviewed knowledge package.

Safety boundary:
- This module never treats generated model text as a factual source.
- Non-Din topics are grounded only in the existing local MEB/MEBİ page
  bundle index.
- TYT Din Kültürü topics are grounded only in current official MEB TYMM
  programme pages and cached locally after first retrieval.
- Topic/subtopic metadata is used only for source retrieval/navigation.
- If a relevant official excerpt cannot be found, the lesson stays blocked.

This path is deliberately separate from the canonical release gate. It does
not mutate or re-release suspended canonical Biology artifacts.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "data"
LOCAL_PAGE_INDEX = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "local_page_bundle_index.json"
)
TOPIC_SOURCE_MAPPING = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "work_queue"
    / "topic_source_mapping.json"
)
DIN_CACHE = (
    PROJECT_ROOT
    / "local_corpus_extracted"
    / "model1_din_tymm_cache.json"
)

# Current official MEB Türkiye Yüzyılı Maarif Modeli pages.
# These URLs are source anchors, not model-authored teaching content.
DIN_SOURCE_URLS = {
    "Bilgi ve İnanç": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/139",
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/140",
    ],
    "Din ve İslam": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/140",
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/150",
    ],
    "İslam ve İbadet": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/141",
    ],
    "Gençlik ve Değerler": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/142",
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/143",
    ],
    "Gönül Coğrafyamız": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/151",
    ],
    "Allah İnsan İlişkisi": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/139",
    ],
    "Hz. Muhammed ve Gençlik": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/143",
    ],
    "Din ve Hayat": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/147",
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/155",
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/150",
    ],
    "Ahlaki Tutum ve Davranışlar": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/142",
    ],
    "İslam Düşüncesinde Yorumlar": [
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/148",
        "https://tymm.meb.gov.tr/din-kulturu-ve-ahlak-bilgisi-dersi-2/unite/157",
    ],
}


# Phase MODEL-1 bulk completion: two curriculum labels do not have a
# one-to-one page in their same exam/source family. These are explicit,
# reviewed cross-family bridges over official local MEBİ pages.
#
# They do NOT reclassify the curriculum record and they do NOT make the
# source canonical. They only provide bounded official excerpts for the
# MODEL-1 fallback path.
SPECIAL_LOCAL_SOURCE_BRIDGES = {
    (
        "AYT",
        "Matematik",
        "Permütasyon Kombinasyon ve Binom",
    ): [
        (
            "MEBI-TYT-MATEMATIK",
            [70, 71, 72, 74, 77],
        ),
    ],
    (
        "TYT",
        "Türkçe",
        "Sözel Mantık ve Muhakeme",
    ): [
        (
            "MEBI-TYT-TURKCE",
            [33, 118],
        ),
        (
            "MEBI-TYT-MATEMATIK",
            [55, 60],
        ),
    ],
}

STOPWORDS = {
    "ve", "ile", "icin", "olan", "olarak", "temel", "konu",
    "bilgi", "giris", "genel", "sistem", "sistemleri", "turleri",
    "ozellikleri", "kavram", "kavramlar", "yapi", "yapisi",
}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(value) -> str:
    text = str(value or "").strip().casefold()
    replacements = {
        "ı": "i",
        "ç": "c",
        "ğ": "g",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def tokens(value):
    return {
        token
        for token in normalize(value).split()
        if len(token) >= 4 and token not in STOPWORDS
    }


@lru_cache(maxsize=1)
def load_curriculum_records():
    records = []
    for path in sorted(CURRICULUM_DIR.glob("*.json")):
        try:
            items = _read_json(path)
        except Exception:
            continue
        if isinstance(items, list):
            records.extend(items)
    return records


@lru_cache(maxsize=1)
def load_topic_source_mapping():
    if not TOPIC_SOURCE_MAPPING.exists():
        return {"items": []}
    return _read_json(TOPIC_SOURCE_MAPPING)


@lru_cache(maxsize=1)
def load_local_page_index():
    if not LOCAL_PAGE_INDEX.exists():
        return None
    return _read_json(LOCAL_PAGE_INDEX)


def topic_key(record):
    return (
        str(record.get("exam", "")),
        str(record.get("subject", "")),
        str(record.get("topic", "")),
    )


@lru_cache(maxsize=1)
def mapping_index():
    result = {}
    for item in load_topic_source_mapping().get("items", []):
        result[
            (
                str(item.get("exam", "")),
                str(item.get("subject", "")),
                str(item.get("topic", "")),
            )
        ] = item
    return result


@lru_cache(maxsize=1)
def package_index():
    index = load_local_page_index()
    if not index:
        return {}
    return {
        package.get("package_id"): package
        for package in index.get("packages", [])
        if package.get("package_id")
    }


def topic_title_hit_count(page_text, records):
    page_n = normalize(page_text)
    count = 0
    for record in records:
        phrase = normalize(record.get("topic"))
        if phrase and phrase in page_n:
            count += 1
    return count


def score_page(page_text, record, sibling_records=None):
    """Deterministic lexical ranking over official source text."""
    text = str(page_text or "")
    if len(text.strip()) < 120:
        return -1000, 0

    text_n = normalize(text)
    topic = str(record.get("topic", ""))
    topic_n = normalize(topic)
    topic_tokens = tokens(topic)
    subtopics = [str(x) for x in record.get("subtopics", []) if str(x).strip()]

    score = 0
    support_hits = 0

    if topic_n and topic_n in text_n:
        score += 140
        support_hits += 2

    for token in topic_tokens:
        if token in text_n:
            score += 10
            support_hits += 1

    for subtopic in subtopics:
        sub_n = normalize(subtopic)
        if sub_n and sub_n in text_n:
            score += 45
            support_hits += 2
            continue

        sub_tokens = tokens(subtopic)
        if not sub_tokens:
            continue
        overlap = sum(1 for token in sub_tokens if token in text_n)
        coverage = overlap / len(sub_tokens)
        if overlap >= 2 and coverage >= 0.50:
            score += 18 + overlap * 4
            support_hits += 1

    if "icindekiler" in text_n:
        score -= 300

    siblings = sibling_records or []
    if siblings and topic_title_hit_count(text, siblings) >= 5:
        score -= 220

    if len(text) >= 700:
        score += 8

    return score, support_hits


def extract_excerpt(text, record, max_chars=6000):
    """Keep locally relevant windows instead of feeding whole books."""
    text = str(text or "").strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    phrases = [record.get("topic", "")] + list(record.get("subtopics", []))
    phrase_norms = [normalize(x) for x in phrases if normalize(x)]
    key_tokens = set()
    for phrase in phrases:
        key_tokens.update(tokens(phrase))

    scored = []
    for i, line in enumerate(lines):
        line_n = normalize(line)
        line_score = 0
        if any(phrase in line_n for phrase in phrase_norms if len(phrase) >= 5):
            line_score += 20
        line_score += sum(2 for token in key_tokens if token in line_n)
        if line_score:
            scored.append((line_score, i))

    if not scored:
        return text[:max_chars]

    scored.sort(key=lambda item: (-item[0], item[1]))
    selected_indexes = []
    used = set()
    for _, index in scored[:8]:
        for j in range(max(0, index - 4), min(len(lines), index + 9)):
            if j not in used:
                used.add(j)
                selected_indexes.append(j)

    selected_indexes.sort()
    excerpt = "\n".join(lines[i] for i in selected_indexes)
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars]
    return excerpt.strip()


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            value = html.unescape(str(data or "")).strip()
            if value:
                self.parts.append(value)

    def text(self):
        return "\n".join(self.parts)


def _load_din_cache():
    if not DIN_CACHE.exists():
        return {}
    try:
        data = _read_json(DIN_CACHE)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_din_cache(cache):
    DIN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DIN_CACHE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch_official_page(url, allow_network=True, timeout=20):
    cache = _load_din_cache()
    cached = cache.get(url)
    if isinstance(cached, dict) and cached.get("text"):
        return cached["text"]

    if not allow_network:
        return None

    request = Request(
        url,
        headers={"User-Agent": "Personal-AI-Teacher-MODEL1/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")

    parser = _VisibleTextParser()
    parser.feed(raw)
    text = parser.text().strip()
    if not text:
        return None

    cache[url] = {
        "text": text,
        "text_sha256": _sha256_text(text),
        "authority": "T.C. Millî Eğitim Bakanlığı / TYMM",
    }
    _write_din_cache(cache)
    return text


def _subject_siblings(record):
    return [
        item
        for item in load_curriculum_records()
        if item.get("exam") == record.get("exam")
        and item.get("subject") == record.get("subject")
    ]



def _bridge_sources(record):
    """
    Return explicitly reviewed local official-source bridges.

    These bridges exist only for curriculum labels whose teaching content is
    distributed across other official MEBİ topic-summary pages. No generated
    content is introduced here. Missing pages fail closed.
    """
    bridge_specs = SPECIAL_LOCAL_SOURCE_BRIDGES.get(topic_key(record), [])
    if not bridge_specs:
        return []

    packages = package_index()
    sources = []

    for family_id, page_numbers in bridge_specs:
        package = packages.get(family_id)
        if not package:
            continue

        wanted = {int(number) for number in page_numbers}

        for page in package.get("pages", []):
            try:
                page_no = int(page.get("page"))
            except (TypeError, ValueError):
                continue

            if page_no not in wanted:
                continue

            if page.get("text_status") != "READY":
                continue

            page_text = str(page.get("text", "") or "").strip()
            if len(page_text) < 120:
                continue

            excerpt = extract_excerpt(
                page_text,
                record,
                max_chars=3500,
            )
            if len(excerpt) < 120:
                continue

            sources.append(
                {
                    "authority": (
                        "T.C. Millî Eğitim Bakanlığı / "
                        "OGM Materyal / MEBİ"
                    ),
                    "source_kind": (
                        "LOCAL_MEBI_REVIEWED_CROSS_FAMILY_BRIDGE"
                    ),
                    "package_id": family_id,
                    "page": page_no,
                    "source_anchor": page.get("source_anchor"),
                    "html_path": page.get("html_path"),
                    "bridge_for": {
                        "exam": record.get("exam"),
                        "subject": record.get("subject"),
                        "topic": record.get("topic"),
                    },
                    "excerpt": excerpt,
                    "excerpt_sha256": _sha256_text(excerpt),
                }
            )

    order = {}
    cursor = 0
    for family_id, page_numbers in bridge_specs:
        for page_no in page_numbers:
            order[(family_id, int(page_no))] = cursor
            cursor += 1

    sources.sort(
        key=lambda item: order.get(
            (item.get("package_id"), item.get("page")),
            10_000,
        )
    )
    return sources

def _local_sources(record):
    bridge_sources = _bridge_sources(record)
    if bridge_sources:
        return bridge_sources

    mapping = mapping_index().get(topic_key(record))
    if not mapping:
        return []

    family_id = mapping.get("family_id")
    if not family_id:
        return []

    package = package_index().get(family_id)
    if not package:
        return []

    siblings = _subject_siblings(record)
    scored = []
    for page in package.get("pages", []):
        if page.get("text_status") != "READY":
            continue
        text = page.get("text", "")
        score, support_hits = score_page(text, record, siblings)
        if score < 30 or support_hits < 1:
            continue
        scored.append((score, support_hits, page))

    scored.sort(key=lambda item: (-item[0], -item[1], item[2].get("page", 0)))

    sources = []
    for score, support_hits, page in scored[:3]:
        excerpt = extract_excerpt(page.get("text", ""), record)
        if not excerpt:
            continue
        sources.append(
            {
                "authority": "T.C. Millî Eğitim Bakanlığı / OGM Materyal / MEBİ",
                "source_kind": "LOCAL_MEBI_PAGE",
                "package_id": family_id,
                "page": page.get("page"),
                "source_anchor": page.get("source_anchor"),
                "html_path": page.get("html_path"),
                "score": score,
                "support_hits": support_hits,
                "excerpt": excerpt,
                "excerpt_sha256": _sha256_text(excerpt),
            }
        )
    return sources


def _din_sources(record, allow_network=True):
    urls = DIN_SOURCE_URLS.get(str(record.get("topic", "")), [])
    sources = []
    for url in urls:
        try:
            text = fetch_official_page(url, allow_network=allow_network)
        except Exception:
            continue
        if not text:
            continue
        excerpt = extract_excerpt(text, record, max_chars=6500)
        if len(excerpt) < 120:
            continue
        sources.append(
            {
                "authority": "T.C. Millî Eğitim Bakanlığı / TYMM",
                "source_kind": "OFFICIAL_TYMM_PROGRAM_PAGE",
                "url": url,
                "excerpt": excerpt,
                "excerpt_sha256": _sha256_text(excerpt),
            }
        )
    return sources[:3]


def resolve_official_sources(record, allow_network=True):
    if str(record.get("subject", "")).strip().casefold() == "din kültürü".casefold():
        return _din_sources(record, allow_network=allow_network)
    return _local_sources(record)


def resolve_topic_record(question, plan=None):
    question_n = normalize(question)
    matches = []
    for record in load_curriculum_records():
        topic_n = normalize(record.get("topic"))
        if topic_n and topic_n in question_n:
            matches.append((len(topic_n), record))

    if matches:
        matches.sort(key=lambda item: -item[0])
        best_len = matches[0][0]
        best = [record for length, record in matches if length == best_len]
        if len(best) == 1:
            return best[0]

    if plan is not None:
        plan_subject = normalize(getattr(plan, "subject", ""))
        plan_topic = normalize(getattr(plan, "topic", ""))
        for record in load_curriculum_records():
            if (
                normalize(record.get("subject")) == plan_subject
                and normalize(record.get("topic")) == plan_topic
            ):
                return record

    return None


def build_model1_official_context(question, plan=None, allow_network=True):
    record = resolve_topic_record(question, plan)
    if not record:
        return None

    sources = resolve_official_sources(record, allow_network=allow_network)
    if not sources:
        return None

    mapping = mapping_index().get(topic_key(record), {})
    payload = {
        "source": "MODEL1_OFFICIAL_SOURCE_GROUNDED",
        "safety_class": "OFFICIAL_SOURCE_EXCERPT_ONLY",
        "canonical_release": False,
        "exam": record.get("exam"),
        "subject": record.get("subject"),
        "grade": mapping.get("grade") or getattr(plan, "grade", None),
        "topic": record.get("topic"),
        "subtopics": record.get("subtopics", []),
        "source_policy": (
            "Teach only facts directly supported by the official source excerpts. "
            "Topic and subtopic names are navigation metadata, not independent factual evidence. "
            "If the excerpts do not support a requested detail, say that the available official source excerpt is insufficient."
        ),
        "sources": sources,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def source_coverage(allow_network=True):
    results = []
    for record in load_curriculum_records():
        sources = resolve_official_sources(record, allow_network=allow_network)
        results.append(
            {
                "exam": record.get("exam"),
                "subject": record.get("subject"),
                "topic": record.get("topic"),
                "status": "SOURCE_READY" if sources else "MISSING_SOURCE",
                "source_count": len(sources),
            }
        )
    return results
