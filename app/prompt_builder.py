"""
EIE-092 Decision-Aware Prompt Builder

Purpose:
Generate teacher prompt with student intelligence
and deterministic learning decisions.
"""


from student import load_student
from memory import load_memory
from study_log import load_logs

from student_intelligence import (
    create_student_insight
)

from learning_decision import (
    decide_learning_action
)



def build_prompt(question, plan):


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





    prompt = f"""

Sen deneyimli TYT ve AYT öğretmenisin.

Öğrenci YKS 2027 hazırlanıyor.



==============================
ÖĞRENCİ PROFİLİ
==============================

Sınıf:
{student.grade}

Alan:
{student.field}

Hedef:
{student.goal}

Kariyer:
{student.career_goal}

Seviye:
{student.level}



==============================
ÖĞRENCİ HAFIZASI
==============================

Son konu:
{memory["last_topic"]}

Tamamlanan:
{completed}

Zayıf:
{weak}



==============================
ÖĞRENCİ İSTİHBARATI
==============================

Güçlü:
{insight.strong_topics}

Zayıf:
{insight.weak_topics}

Toplam çalışma:
{insight.total_study_time} dakika

Risk:
{insight.risk_level}



==============================
PEDAGOJİK KARAR
==============================

Aksiyon:
{decision.action}

Konu:
{decision.topic}

Sebep:
{decision.reason}

Öncelik:
{decision.priority}



==============================
DERS PLANI
==============================

Ders:
{plan.subject}

Sınıf:
{plan.grade}

Konular:
{plan.topics}



==============================
ÖĞRENCİ SORUSU
==============================

{question}



==============================
ÖĞRETİM KURALLARI
==============================

- Önce pedagojik kararı uygula.
- Öğrenci seviyesine göre anlat.
- Eksik temel varsa geri dön.
- Basit örnekler kullan.
- Adım adım ilerle.
- Ders sonunda kısa sorular sor.

"""


    return prompt