"""
EIE-036 Curriculum Engine

Purpose:
Manage curriculum information and provide
deterministic curriculum decisions.
"""


from topics import CURRICULUM


def get_subject_topics(subject, grade):

    return CURRICULUM.get(subject, {}).get(
        str(grade),
        []
    )


def is_topic_available(subject, grade, topic):

    topics = get_subject_topics(
        subject,
        grade
    )

    return topic in topics


def get_next_topic(subject, grade, current_topic):

    topics = get_subject_topics(
        subject,
        grade
    )

    if current_topic not in topics:
        return None

    index = topics.index(current_topic)

    if index + 1 < len(topics):
        return topics[index + 1]

    return None
def get_previous_topics(subject, grade, current_topic):

    topics = get_subject_topics(
        subject,
        grade
    )

    if current_topic not in topics:
        return []

    index = topics.index(current_topic)

    return topics[:index]