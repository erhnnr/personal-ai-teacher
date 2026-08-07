"""
EID-011 Adaptive Curriculum Planner

Purpose:
Decide next learning action using
student performance + curriculum intelligence.
"""


from curriculum_engine import get_topic_info



def decide_next_action(
    exam,
    subject,
    topic,
    score
):

    topic_info = get_topic_info(
        exam,
        subject,
        topic
    )


    if topic_info is None:

        return {

            "action": "unknown",

            "topic": topic,

            "reason": "Topic not found"

        }



    dependencies = topic_info.get(
        "dependencies",
        []
    )


    next_topics = topic_info.get(
        "next_topics",
        []
    )



    # Weak performance
    if score < 60:


        if dependencies:


            return {

                "action": "review",

                "topic": dependencies[0],

                "reason":
                    "Prerequisite knowledge is weak"

            }



        return {

            "action": "repeat",

            "topic": topic,

            "reason":
                "Topic needs reinforcement"

        }



    # Medium performance
    elif score < 80:


        return {

            "action": "practice",

            "topic": topic,

            "reason":
                "More practice required"

        }



    # Strong performance
    else:


        if next_topics:


            return {

                "action": "advance",

                "topic": next_topics[0],

                "reason":
                    "Topic mastered"

            }



        return {

            "action": "complete",

            "topic": topic,

            "reason":
                "Curriculum completed"

        }