"""
EID-004 Knowledge Engine

Purpose:
Load structured educational knowledge packages.
"""

import json
from pathlib import Path


KNOWLEDGE_DIR = (
    Path(__file__).parent.parent
    / "data"
    / "knowledge"
    / "units"
)



def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def find_knowledge_units():

    units = []


    if not KNOWLEDGE_DIR.exists():

        return units



    for file in KNOWLEDGE_DIR.rglob("concept.json"):

        try:

            units.append(
                load_json(file)
            )

        except Exception:

            continue


    return units



def get_knowledge(
    subject,
    grade,
    topic
):

    units = find_knowledge_units()


    return [

        unit

        for unit in units

        if (
            unit.get("subject") == subject
            and
            unit.get("grade") == grade
            and
            unit.get("topic") == topic
        )

    ]



def get_topic_path(topic):

    for file in KNOWLEDGE_DIR.rglob(
        "concept.json"
    ):

        data = load_json(file)

        if data.get("topic") == topic:

            return file.parent


    return None




def get_related_file(
    topic,
    filename
):

    folder = get_topic_path(topic)


    if not folder:

        return None



    file = folder / filename


    if not file.exists():

        return None



    return load_json(file)



def get_relations(topic):

    return get_related_file(
        topic,
        "relations.json"
    )



def get_mistakes(topic):

    return get_related_file(
        topic,
        "mistakes.json"
    )



def get_examples(topic):

    return get_related_file(
        topic,
        "examples.json"
    )



def get_learning_package(
    subject,
    grade,
    topic
):

    concept = get_knowledge(
        subject,
        grade,
        topic
    )


    if not concept:

        return None



    return {

        "concept": concept[0],

        "relations":
            get_relations(topic),

        "mistakes":
            get_mistakes(topic),

        "examples":
            get_examples(topic)

    }