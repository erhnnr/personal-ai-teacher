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
    Backward-compatible canonical-first resolver.

    build_verified_context(plan) remains unchanged for existing callers
    and tests. Raw-question canonical resolution is attempted first.
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

    return build_verified_context(
        plan
    )

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

    return (
        STRICT_TEACHING_POLICY.strip()
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
            f"'{plan.topic}' konusu için doğrulanmış "
            "ders içeriği henüz hazır değil. "
            "Bu nedenle yerel AI modeli bu konuyu "
            "kendi bilgisinden anlatmayacak."
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
            temperature=LLM_TEMPERATURE,
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