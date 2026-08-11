"""
Module:
EIE-009 Teacher Engine

Purpose:
Communicate with the local LLM through LM Studio.

Architecture:
Verified Knowledge -> Strict Teaching Policy -> Prompt
-> Local LLM Generation

Safety rules:

- No verified knowledge -> no teaching.
- Verified knowledge is the factual boundary.
- The model must not fill missing facts from prior knowledge.
- Unverified analogies, examples, rules, definitions, and claims
  must not be introduced.
- Unexpected foreign writing systems -> response rejected.
"""

import json

from config import (
    MODEL_NAME,
    LLM_TEMPERATURE,
)

from llm import (
    client,
    check_llm_connection,
)

from planner import create_plan
from prompt_builder import build_prompt
from teacher_pipeline import run_lesson
from canonical_release_gate import (
    build_teacher_context,
    build_teacher_context_for_question,
)
from model1_official_source_context import (
    build_model1_official_context,
)


STRICT_TEACHING_POLICY = """
SEN PERSONAL AI TEACHER ÖĞRETMEN MOTORUSUN.

ZORUNLU ÖĞRETİM VE GÜVENLİK KURALLARI:

1. DOĞRULANMIŞ BİLGİ SINIRI
- Sana verilen VERIFIED KNOWLEDGE, bu ders için tek güvenilir
  bilgi kaynağıdır.
- VERIFIED KNOWLEDGE içinde bulunmayan bir tanım, kural,
  istisna, formül, özellik, örnek veya olguyu kendi ön
  bilginden ekleme.
- Eksik bilgi varsa uydurma. Gerekirse açıkça:
  "Bu ayrıntı doğrulanmış ders içeriğinde yer almıyor."
  de.

2. KAVRAM SADAKATİ
- Bir kavramı daha kolay anlatmak için anlamını değiştirme.
- Yaklaşmak, eşit olmak, değer almak, tanımlı olmak gibi
  matematiksel olarak farklı ifadeleri birbirinin yerine
  kullanma.
- Özellikle limit anlatımında limit değeri ile fonksiyonun
  noktadaki değerini birbirine karıştırma.
- "Limit, fonksiyonun o noktada ne olacağını söyler" gibi
  yanıltıcı genellemeler yapma.

3. ANALOJİ KURALI
- VERIFIED KNOWLEDGE içinde açıkça desteklenmeyen analojiler
  üretme.
- Analojinin kavramı bozma riski varsa analoji kullanma.
- Açıklamayı mümkün olduğunca doğrudan kavram, tanım, kural
  ve doğrulanmış örnek üzerinden yap.

4. ÖRNEK KURALI
- VERIFIED KNOWLEDGE içindeki doğrulanmış örnekleri tercih et.
- Yeni bir matematiksel örnek üretmen gerekiyorsa yalnızca
  VERIFIED KNOWLEDGE içindeki kuralların doğrudan ve açık bir
  uygulaması olan, sonucu adım adım kontrol edilebilir bir
  örnek kullan.
- Emin olmadığın bir örneği üretme.
- Soru, çözüm adımları ve sonuç birbiriyle tutarlı olmalı.

5. MATEMATİKSEL DİL
- Notasyonu koru.
- İşlem adımlarını atlama.
- Sonucu vermeden önce gerekli dönüşümü göster.
- x -> a ifadesini "x, a değerine yaklaşırken" biçiminde
  açıkla; "x = a olur" anlamına gelecek biçimde anlatma.
- Türkçe matematik dilini açık, kısa ve doğru kullan.

6. ÖĞRETİM BİÇİMİ
- Önce kavramın özünü açıkla.
- Sonra gerekiyorsa doğrulanmış kuralı ver.
- Ardından doğrulanmış veya güvenli biçimde türetilmiş tek
  bir örnek çöz.
- Gereksiz uzun girişler, hikâyeler ve süslü benzetmeler
  kullanma.
- Öğrenciyi çocuklaştıran veya küçümseyen bir dil kullanma.
- Yanıtı ders kitabı kopyası gibi değil, öğretmen anlatımı
  gibi açık ve düzenli yaz.

7. KONTROL
Yanıtı göndermeden önce sessizce kontrol et:
- VERIFIED KNOWLEDGE dışına çıktım mı?
- Kavramın anlamını değiştirdim mi?
- Formül ve işlem doğru mu?
- Örnek ile sonuç tutarlı mı?
- Gereksiz veya yanıltıcı analoji kullandım mı?

Bu kurallar diğer tüm üslup tercihlerinden önceliklidir.
"""


MODEL1_OFFICIAL_SOURCE_POLICY = """
MODEL-1 RESMÎ KAYNAK MODU:
- VERIFIED KNOWLEDGE içindeki source alanı
  MODEL1_OFFICIAL_SOURCE_GROUNDED ise bu, canonical/human-reviewed
  release anlamına gelmez.
- Bu modda yalnızca sources[].excerpt alanlarındaki resmî MEB/MEBİ/TYMM
  metinleri olgusal bilgi sınırıdır.
- topic ve subtopics alanları yalnızca gezinme/konu belirleme bilgisidir;
  tek başına olgusal kanıt değildir.
- Resmî kaynak alıntısı öğrencinin sorduğu ayrıntıyı desteklemiyorsa
  kendi bilginden tamamlama; mevcut resmî kaynak bağlamının yetersiz
  olduğunu açıkça söyle.
- Askıya alınmış canonical artifactleri bu mod üzerinden yeniden
  yayımlama veya canonical release olmuş gibi sunma.
"""


MODEL1_OFFICIAL_OUTPUT_HARDENING = """
MODEL-1 RESMÎ KAYNAK ÇIKTI KURALI — FAIL-CLOSED ÖĞRETİM:

1. YALNIZCA VERİLEN RESMÎ KAYNAĞI KULLAN
- sources[].excerpt dışında yeni olgusal bilgi ekleme.
- Kendi ön bilginden tanım, örnek, analoji, neden-sonuç, istisna,
  genelleme veya ayrıntı üretme.
- topic/subtopics alanlarını olgusal kanıt gibi kullanma.

2. YENİ ÖRNEK ÜRETME
- Kaynakta açıkça bulunmayan kişi, nesne, şehir, yiyecek, sayı,
  deney, günlük yaşam örneği veya senaryo uydurma.
- Kaynaktaki örnekleri koru; nesne veya terimleri başka kelimelerle
  değiştirme.
- "Örneğin" diye başlayan yeni bir cümle ancak aynı örnek excerpt
  içinde açıkça varsa yazılabilir.

3. TERİM VE ANLAM SADAKATİ
- Kaynaktaki teknik terimleri başka terimlerle değiştirme.
- Verilen bir koşullu önermenin öncülünü veya sonucunu değiştirerek
  yeniden yazma.
- Teknik alanlarda kaynak terminolojisini koru.

4. DERS BİÇİMİ
- Kaynaktaki bilgiyi kısa başlıklar altında sadeleştirerek açıkla.
- Kaynak kapsamı yetersizse:
  "Bu ayrıntı mevcut resmî kaynak bağlamında yer almıyor."
  de ve orada dur.
- Kaynak dışı boşlukları akıcı görünmek için doldurma.

5. SESSİZ SON KONTROL
Her olgusal cümle için:
"Bu cümlenin dayanağını sources[].excerpt içinde gösterebilir miyim?"
Cevap hayırsa o cümleyi çıkar.

ÖNCELİK: doğruluk > akıcılık > kapsam.
"""

class TeacherError(Exception):
    """
    Raised when the teacher engine cannot
    complete a safe local LLM request.
    """


class KnowledgeNotReadyError(TeacherError):
    """
    Raised when a curriculum topic exists but
    its verified teaching content is not ready.
    """


class LanguageSafetyError(TeacherError):
    """
    Raised when the local model produces text
    containing an unexpected writing system.
    """


def contains_disallowed_script(text):
    """
    Detect writing systems that should never
    appear in a Turkish student-facing answer.

    Mathematical symbols and Latin characters
    are intentionally not restricted.
    """

    if not text:
        return False

    disallowed_ranges = (
        # Cyrillic
        (0x0400, 0x052F),

        # Hebrew
        (0x0590, 0x05FF),

        # Arabic
        (0x0600, 0x06FF),
        (0x0750, 0x077F),

        # Japanese Hiragana
        (0x3040, 0x309F),

        # Japanese Katakana
        (0x30A0, 0x30FF),

        # CJK Unified Ideographs
        (0x3400, 0x4DBF),
        (0x4E00, 0x9FFF),

        # Korean Hangul
        (0xAC00, 0xD7AF),
    )

    for character in text:
        code_point = ord(
            character
        )

        for start, end in disallowed_ranges:
            if start <= code_point <= end:
                return True

    return False


def build_verified_context(plan):
    """
    Load safe teaching knowledge for the planned lesson.

    Biology uses Knowledge Factory V2's hash-bound canonical release
    gate and MUST NOT fall back to legacy knowledge.

    Other subjects keep the existing verified legacy pipeline until
    migrated to the same canonical release mechanism.
    """

    try:
        canonical_context = build_teacher_context(
            plan
        )
    except Exception:
        canonical_context = None

    if canonical_context is not None:
        return canonical_context

    if str(plan.subject).strip().casefold() == "biyoloji":
        return None

    try:
        lesson = run_lesson(
            plan.subject,
            plan.grade,
            plan.topic,
        )

    except Exception:
        return None

    if not lesson:
        return None

    knowledge = lesson.get(
        "knowledge"
    )

    if not knowledge:
        return None

    verified_package = {
        "source": "LEGACY_VERIFIED_KNOWLEDGE",
        "subject": lesson.get("subject"),
        "grade": lesson.get("grade"),
        "topic": lesson.get("topic"),
        "knowledge": knowledge,
    }

    return json.dumps(
        verified_package,
        ensure_ascii=False,
        indent=2,
    )


def build_verified_context_for_question(
    plan,
    question,
):
    """
    MODEL-1 source priority:
    1. Canonical released context.
    2. Existing verified legacy context.
    3. Official-source-grounded MODEL-1 fallback.

    The third path never re-releases canonical artifacts; it uses the
    official source excerpts directly as the factual boundary.
    """

    try:
        canonical_context = (
            build_teacher_context_for_question(
                question,
                plan,
            )
        )
    except Exception:
        canonical_context = None

    if canonical_context is not None:
        return canonical_context

    legacy_context = build_verified_context(
        plan
    )

    if legacy_context is not None:
        return legacy_context

    try:
        return build_model1_official_context(
            question,
            plan,
        )
    except Exception:
        return None


def _is_model1_official_context(verified_context):
    if not isinstance(verified_context, str):
        return False

    try:
        payload = json.loads(verified_context)
    except (TypeError, json.JSONDecodeError):
        return False

    return (
        payload.get("source")
        == "MODEL1_OFFICIAL_SOURCE_GROUNDED"
    )

def _official_source_payload(verified_context):
    if not _is_model1_official_context(
        verified_context
    ):
        return None

    try:
        payload = json.loads(verified_context)
    except (TypeError, json.JSONDecodeError):
        return None

    return payload


def _grounding_tokens(value):
    import re
    import unicodedata

    text = str(value or "").casefold()

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

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        ch
        for ch in text
        if not unicodedata.combining(ch)
    )

    words = re.findall(
        r"[a-z0-9]+",
        text,
    )

    stopwords = {
        "anlat",
        "nedir",
        "nasil",
        "konu",
        "konusu",
        "icin",
        "olan",
        "olarak",
        "ve",
        "ile",
        "bir",
        "bu",
    }

    return {
        word
        for word in words
        if len(word) >= 3
        and word not in stopwords
    }


def _official_excerpt_chunks(excerpt):
    import re

    text = str(excerpt or "").replace(
        "\r\n",
        "\n",
    )

    chunks = []

    for raw_line in text.split("\n"):
        line = " ".join(
            raw_line.strip().split()
        )

        if len(line) < 20:
            continue

        if line.startswith(
            ("http://", "https://")
        ):
            continue

        pieces = re.split(
            r"(?<=[.!?])\s+",
            line,
        )

        for piece in pieces:
            piece = piece.strip()

            if len(piece) < 20:
                continue

            if (
                len(piece.split()) >= 8
                and not piece.endswith(
                    (
                        ".",
                        "!",
                        "?",
                        ":",
                        ";",
                        ")",
                        "]",
                        "}",
                    )
                )
                and "=" not in piece
            ):
                continue

            chunks.append(piece)

    return chunks


def _build_model1_official_extractive_answer(
    question,
    verified_context,
):
    payload = _official_source_payload(
        verified_context
    )

    if not payload:
        return None

    sources = payload.get(
        "sources",
        [],
    )

    if not isinstance(sources, list):
        return None

    query_tokens = _grounding_tokens(
        question
    )

    navigation_tokens = set(
        _grounding_tokens(
            payload.get("topic", "")
        )
    )

    for subtopic in payload.get(
        "subtopics",
        [],
    ):
        navigation_tokens.update(
            _grounding_tokens(
                subtopic
            )
        )

    candidates = []
    seen = set()

    for source_index, source in enumerate(
        sources
    ):
        excerpt = source.get(
            "excerpt",
            "",
        )

        for chunk_index, chunk in enumerate(
            _official_excerpt_chunks(
                excerpt
            )
        ):
            normalized = " ".join(
                chunk.casefold().split()
            )

            if normalized in seen:
                continue

            seen.add(normalized)

            chunk_tokens = _grounding_tokens(
                chunk
            )

            query_overlap = len(
                query_tokens
                & chunk_tokens
            )

            navigation_overlap = len(
                navigation_tokens
                & chunk_tokens
            )

            score = (
                query_overlap * 6
                + navigation_overlap * 2
            )

            candidates.append(
                (
                    score,
                    source_index,
                    chunk_index,
                    chunk,
                    source,
                )
            )

    if not candidates:
        return (
            "Bu ayrıntı mevcut resmî kaynak "
            "bağlamında yer almıyor."
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1],
            item[2],
        )
    )

    selected = []
    total_chars = 0

    for candidate in candidates:
        _, _, _, chunk, _ = candidate

        if selected and (
            total_chars + len(chunk) > 5200
        ):
            continue

        selected.append(
            candidate
        )
        total_chars += len(chunk)

        if len(selected) >= 14:
            break

    selected.sort(
        key=lambda item: (
            item[1],
            item[2],
        )
    )

    topic = str(
        payload.get(
            "topic",
            "Resmî Kaynak Dersi",
        )
    ).strip()

    lines = [
        f"### {topic}",
        "",
        (
            "Bu ders MODEL-1'de resmî MEB/MEBİ/TYMM "
            "kaynak metninden doğrudan sunulmaktadır."
        ),
        (
            "Aşağıdaki olgusal ifadeler yerel AI tarafından "
            "yeniden yazılmamıştır."
        ),
        "",
    ]

    current_source = None

    for _, source_index, _, chunk, source in selected:
        if source_index != current_source:
            current_source = source_index

            authority = str(
                source.get(
                    "authority",
                    "T.C. Millî Eğitim Bakanlığı",
                )
            ).strip()

            page = source.get("page")

            if page is not None:
                label = (
                    f"#### Resmî Kaynak — {authority} "
                    f"(sayfa {page})"
                )
            else:
                label = (
                    f"#### Resmî Kaynak — {authority}"
                )

            lines.extend(
                [
                    label,
                    "",
                ]
            )

        lines.extend(
            [
                chunk,
                "",
            ]
        )

    lines.extend(
        [
            "### Kontrol Sorusu",
            "",
            (
                "Yukarıdaki resmî kaynak metnine göre "
                "konunun temel noktalarından birini "
                "kendi cümlelerinle açıklar mısın?"
            ),
        ]
    )

    return "\n".join(
        lines
    ).strip()

def build_system_prompt(
    question,
    plan,
    verified_context,
):
    """
    Combine the existing lesson prompt with the
    non-negotiable verified-knowledge teaching policy.
    """

    lesson_prompt = build_prompt(
        question,
        plan,
        verified_context=verified_context,
    )

    policies = [
        STRICT_TEACHING_POLICY.strip(),
        MODEL1_OFFICIAL_SOURCE_POLICY.strip(),
    ]

    if _is_model1_official_context(
        verified_context
    ):
        policies.append(
            MODEL1_OFFICIAL_OUTPUT_HARDENING.strip()
        )

    return (
        "\n\n".join(policies)
        + "\n\n"
        + "AŞAĞIDA MEVCUT DERS PROMPTU VE "
        + "VERIFIED KNOWLEDGE BAĞLAMI BULUNUYOR:\n\n"
        + lesson_prompt
    )

def ask_teacher(question):
    """
    Answer a student question using verified educational
    knowledge and the local LM Studio model.
    """

    if not isinstance(question, str):
        raise TeacherError(
            "Question must be a string."
        )

    question = question.strip()

    if not question:
        raise TeacherError(
            "Question cannot be empty."
        )

    plan = create_plan(
        question
    )

    verified_context = build_verified_context_for_question(
        plan,
        question,
    )

    if verified_context is None:
        raise KnowledgeNotReadyError(
            f"'{plan.topic}' konusu için doğrulanmış veya "
            "resmî kaynak-temelli ders bağlamı bulunamadı. "
            "Bu nedenle yerel AI modeli bu konuyu "
            "kendi bilgisinden anlatmayacak."
        )

    if _is_model1_official_context(
        verified_context
    ):
        extractive_answer = (
            _build_model1_official_extractive_answer(
                question,
                verified_context,
            )
        )

        if extractive_answer:
            return extractive_answer

        raise KnowledgeNotReadyError(
            f"'{plan.topic}' konusu için resmî kaynak "
            "bulundu ancak öğrenciye güvenle sunulabilir "
            "tam bir kaynak parçası çıkarılamadı."
        )

    connection = check_llm_connection()

    if not connection["connected"]:
        raise TeacherError(
            "LM Studio connection is not available. "
            f"Details: {connection['error']}"
        )

    available_models = connection["models"]

    if MODEL_NAME not in available_models:
        raise TeacherError(
            f"Configured model '{MODEL_NAME}' "
            "is not available in LM Studio."
        )

    try:
        prompt = build_system_prompt(
            question,
            plan,
            verified_context,
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            temperature=(
                0.0
                if _is_model1_official_context(
                    verified_context
                )
                else LLM_TEMPERATURE
            ),
        )

        if not response.choices:
            raise TeacherError(
                "The local model returned no response."
            )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            raise TeacherError(
                "The local model returned an empty response."
            )

        content = content.strip()

        if contains_disallowed_script(
            content
        ):
            raise LanguageSafetyError(
                "Yerel model Türkçe dışı bir yazı sistemi "
                "kullandı. Yanıt güvenlik nedeniyle "
                "öğrenciye gösterilmedi."
            )

        return content

    except TeacherError:
        raise

    except Exception as exc:
        raise TeacherError(
            f"Local teacher request failed: {exc}"
        ) from exc