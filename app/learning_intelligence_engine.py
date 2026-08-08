"""
EID-014 Learning Intelligence Engine

Purpose:
Combine student intelligence,
curriculum intelligence and adaptive decisions.
"""


from student_intelligence_v2 import (
    analyze_topic_result
)

from curriculum_engine import (
    get_topic_info
)



def decide_learning_action(
    exam,
    subject,
    topic,
    score,
    attempts=1
):

    student_state = analyze_topic_result(
        topic,
        score,
        attempts
    )


    curriculum_state = get_topic_info(
        exam,
        subject,
        topic
    )


    if curriculum_state is None:

        return {

            "decision": "unknown",

            "reason":
                "Curriculum data not found"

        }



    mastery = student_state["mastery"]



    if mastery < 0.6:

        decision = "review"


        target = (
            curriculum_state
            .get("dependencies", [])
        )


        reason = (
            "Topic mastery is low. "
            "Review prerequisites."
        )



    elif mastery < 0.8:

        decision = "practice"


        target = topic


        reason = (
            "Topic developing. "
            "Need more exercises."
        )



    else:

        decision = "advance"


        next_topics = (
            curriculum_state
            .get("next_topics", [])
        )


        target = (
            next_topics[0]
            if next_topics
            else None
        )


        reason = (
            "Topic mastered. "
            "Move forward."
        )



    return {

        "topic": topic,

        "mastery":
            mastery,

        "decision":
            decision,

        "target":
            target,

        "reason":
            reason

    }