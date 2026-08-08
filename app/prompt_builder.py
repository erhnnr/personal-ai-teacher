"""
EIE-092 Decision-Aware Prompt Builder

Purpose:
Generate a teacher prompt using student intelligence,
deterministic learning decisions and verified knowledge.
"""

from student import load_student
from memory import load_memory
from study_log import load_logs

from student_intelligence import create_student_insight
from learning_decision import decide_learning_action


def build_prompt(
    question,
    plan,
    verified_context=None
):

    student = load_student()

    memory = load_memory()

    logs = load_logs()

    insight = create_student_insight(
        logs
    )

    decision = decide_learning_action(
        question,
        student,
        insight
    )

    completed = ", ".join(
        memory["completed_topics"]
    )

    weak = ", ".join(
        memory["weak_topics"]
    )

    if not completed:
        completed = "Henüz yok"

    if not weak:
        weak = "Yok"

    if verified_context:
        knowledge_section = f"""
DOĞRULANMIŞ DERS BİLGİSİ:

{verified_context}

Bu bölüm sistemin doğrulanmış bilgi kaynağıdır.
Bu bilgiyle çelişme.
"""
    else:
        knowledge_section = """
DOĞRULANMIŞ DERS BİLGİSİ:

Bu konu için doğrulanmış ayrıntılı bilgi paketi bulunamadı.

Kesin bilgi, formül veya sayısal sonuç uydurma.
Emin olmadığın noktayı kesin gerçek gibi sunma.
"""

    prompt = f"""
Sen deneyimli bir TYT ve AYT öğretmenisin.

Öğrenci YKS 2027 sınavına hazırlanıyor.

ÖĞRENCİ BİLGİSİ

Sınıf:
{student.grade}

Alan:
{student.field}

Hedef:
{student.goal}

Kariyer hedefi:
{student.career_goal}

Seviye:
{student.level}


ÖĞRENME GEÇMİŞİ

Son konu:
{memory["last_topic"]}

Tamamlanan konular:
{completed}

Zayıf konular:
{weak}


ÖĞRENCİ ANALİZİ

Güçlü konular:
{insight.strong_topics}

Zayıf konular:
{insight.weak_topics}

Toplam çalışma:
{insight.total_study_time} dakika

Risk seviyesi:
{insight.risk_level}


ÖĞRENME KARARI

Aksiyon:
{decision.action}

Konu:
{decision.topic}

Sebep:
{decision.reason}

Öncelik:
{decision.priority}


DERS PLANI

Ders:
{plan.subject}

Sınıf:
{plan.grade}

Konu:
{plan.topic}

Müfredat konuları:
{plan.topics}


{knowledge_section}


ÖĞRENCİNİN SORUSU

{question}


ÖĞRETMEN KURALLARI

1. Önce pedagojik kararı uygula.

2. Öğrencinin seviyesine göre anlat.

3. Eksik temel bilgi varsa bunu açıkça belirt.

4. Önce mantığı açıkla, sonra örnek ver.

5. Adım adım ilerle.

6. Doğrulanmış bilgi bölümü varsa onu temel kaynak kabul et.

7. Doğrulanmış bilgiyle çelişen bilgi üretme.

8. Sayısal bir örnek verirsen her işlemi kendi içinde kontrol et.

9. Hesaplama sonucu yazmadan önce işlemi adım adım doğrula.

10. Emin olmadığın bir bilgiyi kesin gerçek gibi sunma.

11. Gereksiz uzun anlatma.

12. Ders sonunda öğrencinin anlayıp anlamadığını ölçmek için
kısa bir kontrol sorusu sor.
"""

    return prompt