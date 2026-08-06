"""
EID-008 Learning Loop

Purpose:
Connect evaluation results with learning decisions.
"""


from dataclasses import dataclass, field



@dataclass
class LearningDecision:

    topic: str

    status: str

    recommendation: str

    mistakes: list = field(
        default_factory=list
    )



def analyze_result(
    evaluation_result,
    topic
):

    mistakes = []


    if evaluation_result.wrong_answers > 0:

        mistakes.append(
            "Konuda tekrar ihtiyacı var"
        )


    if evaluation_result.mastery_level == "weak":

        recommendation = (
            "Konu temelleri tekrar edilmeli."
        )

    elif evaluation_result.mastery_level == "developing":

        recommendation = (
            "Eksik noktalar için ek soru çözülmeli."
        )

    else:

        recommendation = (
            "Yeni seviyeye geçilebilir."
        )


    return LearningDecision(

        topic=topic,

        status=
            evaluation_result.mastery_level,

        recommendation=recommendation,

        mistakes=mistakes

    )