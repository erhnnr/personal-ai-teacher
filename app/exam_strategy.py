"""
EIE-050 Exam Strategy Engine

Purpose:
Create YKS preparation strategy.
"""


from dataclasses import dataclass



@dataclass
class ExamStrategy:

    priority: str

    focus_subjects: list

    daily_plan: list

    reason: str





def calculate_exam_phase(target_year):

    current_year = 2026


    remaining = target_year - current_year


    if remaining >= 1:

        return "foundation"


    elif remaining == 0:

        return "intensive"


    else:

        return "exam_ready"





def create_exam_strategy(student):


    phase = calculate_exam_phase(
        student.target_year
    )


    focus = []


    plan = []



    if student.field == "Sayısal":


        focus.extend([

            "Matematik",

            "Fizik",

            "Kimya",

            "Biyoloji"

        ])



    if "Tıp" in student.career_goal:


        reason = (
            "Tıp hedefi nedeniyle "
            "yüksek sayısal başarı gerekiyor."
        )


    else:


        reason = (
            "Sayısal alan hedeflerine göre "
            "ders dengesi oluşturuldu."
        )




    if phase == "foundation":


        plan = [

            "TYT temel eksikleri kapat",

            "Matematik temelini güçlendir",

            "AYT konularına kontrollü başla"

        ]



    elif phase == "intensive":


        plan = [

            "AYT ağırlıklı çalışma",

            "Deneme analizi",

            "Eksik konu kapatma"

        ]



    else:


        plan = [

            "Deneme",

            "Hız çalışması",

            "Son tekrar"

        ]




    return ExamStrategy(

        priority=phase,

        focus_subjects=focus,

        daily_plan=plan,

        reason=reason

    )