"""
EIE-019 Progress Engine

Purpose:
Track student learning progress.
"""


import json
from pathlib import Path


PROGRESS_FILE = Path(__file__).parent.parent / "data" / "progress.json"



DEFAULT_PROGRESS = {
    "topics": {}
}



def load_progress():

    if not PROGRESS_FILE.exists():

        save_progress(DEFAULT_PROGRESS)

        return DEFAULT_PROGRESS.copy()


    with open(
        PROGRESS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def save_progress(progress):

    with open(
        PROGRESS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            progress,
            f,
            indent=4,
            ensure_ascii=False
        )



def update_topic_progress(topic, score):

    progress = load_progress()


    if topic not in progress["topics"]:

        progress["topics"][topic] = {

            "attempts": 0,

            "best_score": 0,

            "last_score": 0

        }


    data = progress["topics"][topic]


    data["attempts"] += 1

    data["last_score"] = score


    if score > data["best_score"]:

        data["best_score"] = score


    save_progress(progress)


    return data