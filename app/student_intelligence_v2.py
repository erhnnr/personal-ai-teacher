"""
EID-013 Student Intelligence 2.0

Purpose:
Track student mastery and learning history.
"""


def calculate_mastery(score):

    mastery = score / 100

    if mastery < 0:
        return 0

    if mastery > 1:
        return 1

    return mastery



def analyze_topic_result(
    topic,
    score,
    attempts=1
):

    mastery = calculate_mastery(
        score
    )


    if mastery < 0.6:

        status = "weak"

        review_needed = True


    elif mastery < 0.8:

        status = "developing"

        review_needed = True


    else:

        status = "mastered"

        review_needed = False



    return {

        "topic": topic,

        "score": score,

        "mastery": mastery,

        "attempts": attempts,

        "status": status,

        "review_needed":
            review_needed

    }