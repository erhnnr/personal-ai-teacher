"""
EIE-037 Adaptive Planner

Purpose:
Create deterministic learning decisions.
"""

from dataclasses import dataclass


@dataclass
class AdaptivePlan:

    action: str
    topic: str
    reason: str



def create_adaptive_plan(
    student,
    progress,
    memory,
    curriculum
):

    current_topic = student.current_topic


    if current_topic in student.weak_topics:

        return AdaptivePlan(
            action="review",
            topic=current_topic,
            reason="Konu zayıf olarak işaretlenmiş."
        )


    topic_progress = progress.get(
        "topics",
        {}
    ).get(
        current_topic,
        {}
    )


    best_score = topic_progress.get(
        "best_score",
        0
    )


    if best_score > 0 and best_score < 70:

        return AdaptivePlan(
            action="review",
            topic=current_topic,
            reason="Başarı skoru düşük."
        )


    if best_score >= 80:

        next_topic = curriculum.get_next_topic(
            "Matematik",
            student.grade,
            current_topic
        )


        if next_topic:

            return AdaptivePlan(
                action="next_topic",
                topic=next_topic,
                reason="Konu başarıyla tamamlandı."
            )


    return AdaptivePlan(
        action="continue",
        topic=current_topic,
        reason="Öğrenme devam ediyor."
    )