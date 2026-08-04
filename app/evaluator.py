"""
EIE-018 Evaluator Engine

Purpose:
Evaluate quiz answers and analyze learning status.
"""


from dataclasses import dataclass, field



@dataclass
class EvaluationResult:

    total_questions: int

    correct_answers: int

    wrong_answers: int

    score: float

    mastery_level: str = ""

    recommendation: str = ""

    weak_topics: list = field(default_factory=list)



def analyze_mastery(score):

    if score >= 90:

        return (
            "mastered",
            "Konu iyi öğrenilmiş. Daha zor seviye sorulara geçilebilir."
        )


    elif score >= 75:

        return (
            "good",
            "Temel bilgiler oturmuş. Eksik noktalar güçlendirilmeli."
        )


    elif score >= 50:

        return (
            "developing",
            "Konu kısmen anlaşılmış. Tekrar ve orta seviye soru çözümü gerekli."
        )


    else:

        return (
            "weak",
            "Temel kavramlar tekrar edilmeli ve konu yeniden çalışılmalı."
        )



def evaluate_quiz(quiz, student_answers):

    total = len(quiz.questions)

    correct = 0

    wrong = 0


    for index, answer in enumerate(student_answers):

        if index < len(quiz.answers):

            if answer == quiz.answers[index]:

                correct += 1

            else:

                wrong += 1



    score = 0


    if total > 0:

        score = (correct / total) * 100



    mastery_level, recommendation = analyze_mastery(
        score
    )


    weak_topics = []


    if score < 75:

        weak_topics.append(
            quiz.topic
        )


    return EvaluationResult(

        total_questions=total,

        correct_answers=correct,

        wrong_answers=wrong,

        score=score,

        mastery_level=mastery_level,

        recommendation=recommendation,

        weak_topics=weak_topics

    )