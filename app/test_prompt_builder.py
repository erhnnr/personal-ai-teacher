from prompt_builder import build_prompt
from lesson_plan import LessonPlan
from student import load_student


student = load_student()


plan = LessonPlan(
    student=student,
    subject="Matematik",
    grade=str(student.grade),
    topics=[
        "Fonksiyonlar"
    ],
    question="Fonksiyonlar konusunu anlat."
)


prompt = build_prompt(
    "Fonksiyonlar konusunu anlat.",
    plan
)


print(prompt)