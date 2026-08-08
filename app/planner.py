"""
EIE-011 Planner Engine

Purpose:
Create deterministic lesson plans.

Topic detection:
Use the curriculum topic detector first.
Only use text cleanup as a fallback when
no curriculum topic can be detected.
"""

from student import load_student
from curriculum_engine import get_subject_topics
from lesson_plan import LessonPlan
from subject_detector import detect_subject
from topic_detector import detect_topic


def extract_fallback_topic(question):
    """
    Fallback topic extraction.

    This is used only when the deterministic
    curriculum topic detector cannot identify
    a known topic.
    """

    topic = question.strip()

    cleanup_phrases = (
        "konusunu anlat.",
        "konusunu anlat",
        "anlat.",
        "anlat",
    )

    lower_topic = topic.lower()

    for phrase in cleanup_phrases:

        if lower_topic.endswith(
            phrase
        ):
            topic = topic[
                :len(topic) - len(phrase)
            ].strip()

            break

    if not topic:
        return question.strip()

    return topic.capitalize()


def create_plan(question):

    student = load_student()

    detected_topic = detect_topic(
        question
    )

    detected_subject = (
        detected_topic.get("subject")
        if detected_topic
        else None
    )

    detected_topic_name = (
        detected_topic.get("topic")
        if detected_topic
        else None
    )

    subject = (
        detected_subject
        or detect_subject(question)
    )

    grade = str(
        student.grade
    )

    topics = get_subject_topics(
        subject,
        grade
    )

    topic = (
        detected_topic_name
        or extract_fallback_topic(question)
    )

    plan = LessonPlan(
        student=student,
        subject=subject,
        grade=grade,
        topics=topics,
        question=question,
        topic=topic,
        goal=(
            "Öğrencinin konuyu anlamasını sağlamak"
        ),
    )

    if topic.lower() == "limit":

        if student.grade < 12:

            plan.allowed = False

            plan.reason = (
                "Limit konusu henüz bu sınıf "
                "seviyesinde değil."
            )

            plan.next_topic = (
                "Fonksiyonlar"
            )

    return plan