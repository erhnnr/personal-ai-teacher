"""
EIE-091 Learning Decision Engine

Purpose:
Make deterministic learning decisions before LLM response.
"""


from dataclasses import dataclass



@dataclass
class LearningDecision:

    action: str

    topic: str

    reason: str

    priority: str





def check_topic_prerequisite(
    topic,
    student
):


    prerequisites = {

        "Limit": [
            "Fonksiyonlar"
        ],

        "Türev": [
            "Limit",
            "Fonksiyonlar"
        ],

        "İntegral": [
            "Türev"
        ]

    }



    required = prerequisites.get(
        topic,
        []
    )



    for item in required:


        if item in student.weak_topics:


            return item



    return None





def decide_learning_action(
    question,
    student,
    insight
):


    question_lower = (
        question.lower()
    )



    topic = None



    if "limit" in question_lower:

        topic = "Limit"



    elif "türev" in question_lower:

        topic = "Türev"



    elif "fonksiyon" in question_lower:

        topic = "Fonksiyonlar"



    else:

        topic = "Genel"



    missing = check_topic_prerequisite(
        topic,
        student
    )



    if missing:


        return LearningDecision(

            action="review_prerequisite",

            topic=missing,

            reason=
            f"{topic} için önce {missing} güçlendirilmeli.",

            priority="high"

        )




    if topic in insight.weak_topics:


        return LearningDecision(

            action="review",

            topic=topic,

            reason=
            "Bu konu öğrencinin zayıf alanında.",

            priority="medium"

        )





    return LearningDecision(

        action="teach",

        topic=topic,

        reason=
        "Konu öğrenmeye uygun.",

        priority="normal"

    )