"""
EIE-031 Quiz Generator Hybrid

Purpose:
Generate quizzes using LLM with fallback support.
"""


from quiz import create_quiz, add_question
from lesson_plan import LessonPlan


def extract_topic(source):

    if isinstance(source, LessonPlan):

        topic = source.topic

        if not topic:

            topic = (
                source.topics[0]
                if source.topics
                else "Genel"
            )

        return topic


    return source



def generate_quiz(source):

    topic = extract_topic(source)


    quiz = create_quiz(
        topic
    )


    try:

        from quiz_llm import generate_question


        question = generate_question(
            topic
        )


        add_question(
            quiz,
            question,
            ""
        )


    except Exception:


        add_question(
            quiz,
            f"{topic} konusu ile ilgili temel soru 1",
            "cevap1"
        )


        add_question(
            quiz,
            f"{topic} konusu ile ilgili temel soru 2",
            "cevap2"
        )


        add_question(
            quiz,
            f"{topic} konusu ile ilgili temel soru 3",
            "cevap3"
        )


    return quiz