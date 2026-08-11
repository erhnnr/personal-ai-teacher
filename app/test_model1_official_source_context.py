import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import model1_official_source_context as source


def record():
    return {
        "exam": "AYT",
        "subject": "Biyoloji",
        "topic": "Sinir Sistemi",
        "subtopics": ["Nöron", "İmpuls oluşumu ve iletimi"],
    }


def test_score_prefers_topic_and_subtopic_content():
    good = "SINIR SISTEMI\nNöron yapısı ve impuls oluşumu ile iletimi açıklanır. " * 20
    weak = "Biyoloji konu özetleri içindekiler. Sinir Sistemi. " * 20

    good_score, good_hits = source.score_page(good, record(), [record()])
    weak_score, _ = source.score_page(weak, record(), [record()])

    assert good_score > weak_score
    assert good_hits >= 3


def test_extract_excerpt_keeps_relevant_text():
    text = ("Uzak içerik\n" * 300) + "Nöron ve impuls oluşumu burada açıklanır.\n" + ("Uzak içerik\n" * 300)
    excerpt = source.extract_excerpt(text, record(), max_chars=1200)
    assert "Nöron" in excerpt
    assert len(excerpt) <= 1200


def test_raw_question_exact_topic_wins(monkeypatch):
    records = [
        record(),
        {"exam": "AYT", "subject": "Biyoloji", "topic": "Dolaşım Sistemleri", "subtopics": []},
    ]
    monkeypatch.setattr(source, "load_curriculum_records", lambda: records)
    resolved = source.resolve_topic_record(
        "Sinir Sistemi konusu çalışılıyor. Öğrencinin sorusu: Nöron nedir?"
    )
    assert resolved["topic"] == "Sinir Sistemi"


def test_context_is_official_source_bounded(monkeypatch):
    monkeypatch.setattr(source, "load_curriculum_records", lambda: [record()])
    monkeypatch.setattr(source, "mapping_index", lambda: {})
    monkeypatch.setattr(
        source,
        "resolve_official_sources",
        lambda *_args, **_kwargs: [
            {
                "authority": "MEB",
                "source_kind": "LOCAL_MEBI_PAGE",
                "excerpt": "Nöron resmi kaynak metni.",
                "excerpt_sha256": "x",
            }
        ],
    )
    payload = json.loads(
        source.build_model1_official_context("Sinir Sistemi konusunu anlat.")
    )
    assert payload["source"] == "MODEL1_OFFICIAL_SOURCE_GROUNDED"
    assert payload["canonical_release"] is False
    assert payload["sources"][0]["authority"] == "MEB"
