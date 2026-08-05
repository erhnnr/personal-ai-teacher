"""
EIE-070 Study Log Engine

Purpose:
Record real student study activity.
"""


import json
from pathlib import Path
from datetime import datetime



LOG_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "student"
    / "study_log.json"
)



DEFAULT_LOG = []



def load_logs():

    if not LOG_FILE.exists():

        save_logs(DEFAULT_LOG)

        return []


    with open(
        LOG_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)




def save_logs(logs):

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            logs,
            f,
            ensure_ascii=False,
            indent=4
        )





def add_study_record(
    subject,
    topic,
    duration,
    score=None
):


    logs = load_logs()


    record = {

        "date":
            datetime.now().strftime(
                "%Y-%m-%d"
            ),

        "subject":
            subject,

        "topic":
            topic,

        "duration":
            duration,

        "score":
            score

    }


    logs.append(record)


    save_logs(logs)


    return record





def get_topic_history(topic):


    logs = load_logs()


    return [

        item

        for item in logs

        if item["topic"] == topic

    ]





def calculate_total_time():


    logs = load_logs()


    return sum(

        item["duration"]

        for item in logs

    )