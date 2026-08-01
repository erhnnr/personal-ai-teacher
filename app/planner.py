"""
EIE-011 Planner Engine

Purpose:
Create deterministic lesson plans.
"""

from student import load_student
from curriculum_engine import get_subject_topics
from lesson_plan import LessonPlan
from subject_detector import detect_subject


def create_plan(question):

    student = load_student()

    subject = detect_subject(question)

    grade = str(student.grade)

    topics = get_subject_topics(subject, grade)

    topic = question.lower()

    topic = (
        topic
        .replace("konusunu anlat.", "")
        .replace("konusunu anlat", "")
        .replace("anlat.", "")
        .replace("anlat", "")
        .strip()
        .capitalize()
    )


    plan = LessonPlan(
        student=student,
        subject=subject,
        grade=grade,
        topics=topics,
        question=question,
        topic=topic,
        goal="Öğrencinin konuyu anlamasını sağlamak"
    )


    if "limit" in question.lower():

        if student.grade < 12:

            plan.allowed = False

            plan.reason = "Limit konusu henüz bu sınıf seviyesinde değil."

            plan.next_topic = "Fonksiyonlar"


    return plan