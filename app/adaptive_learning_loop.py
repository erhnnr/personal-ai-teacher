"""
EID-012 Adaptive Learning Loop

Purpose:
Connect evaluation results with adaptive curriculum decisions.
"""


from adaptive_curriculum import decide_next_action



def process_learning_result(
    exam,
    subject,
    topic,
    score
):

    decision = decide_next_action(
        exam,
        subject,
        topic,
        score
    )


    return {

        "current_topic": topic,

        "score": score,

        "next_action":
            decision["action"],

        "recommended_topic":
            decision["topic"],

        "reason":
            decision["reason"]

    }