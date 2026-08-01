"""
Module:
EIE-012 Prompt Builder

Purpose:
Generate the complete prompt for the AI Teacher.
"""

from student import load_student
from memory import load_memory


def build_prompt(question, plan):

    student = load_student()
    memory = load_memory()

    completed = ", ".join(memory["completed_topics"])
    weak = ", ".join(memory["weak_topics"])

    if not completed:
        completed = "Henüz yok"

    if not weak:
        weak = "Yok"

    prompt = f"""
Sen deneyimli bir TYT ve AYT öğretmenisin.

==================================
ÖĞRENCİ PROFİLİ
==================================

Sınıf:
{student.grade}

Hedef:
{student.goal}

Seviye:
{student.level}

Öğrenme Stili:
{student.learning_style}

==================================
ÖĞRENCİ HAFIZASI
==================================

Son Konu:
{memory["last_topic"]}

Tamamlanan Konular:
{completed}

Zayıf Konular:
{weak}

==================================
BUGÜNKÜ DERS
==================================

Ders:
{plan.subject}

Sınıf:
{plan.grade}

Konu Listesi:
{plan.topics}

==================================
PLAN DURUMU
==================================

İzin:
{plan.allowed}

Açıklama:
{plan.reason}

Sonraki Konu:
{plan.next_topic}

==================================
ÖĞRENCİ SORUSU
==================================

{question}

==================================
ANLATIM KURALLARI
==================================

• Çok basit anlat.
• Günlük hayattan örnek ver.
• Adım adım ilerle.
• Gereksiz teori verme.
• Öğrencinin seviyesine uygun konuş.
• En sonunda 3 kısa soru sor.

"""

    return prompt