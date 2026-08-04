"""
EIE-080 Student Intelligence Engine

Purpose:
Analyze student behavior and generate insights.
"""


from dataclasses import dataclass



@dataclass
class StudentInsight:

    strong_topics: list

    weak_topics: list

    total_study_time: int

    risk_level: str

    recommendation: str





def analyze_study(logs):


    topic_scores = {}

    topic_times = {}



    for item in logs:


        topic = item["topic"]


        duration = item["duration"]


        score = item.get(
            "score"
        )



        topic_times[topic] = (
            topic_times.get(topic, 0)
            + duration
        )


        if score is not None:


            if topic not in topic_scores:

                topic_scores[topic] = []


            topic_scores[topic].append(
                score
            )



    strong = []

    weak = []



    for topic, scores in topic_scores.items():


        average = (
            sum(scores)
            /
            len(scores)
        )



        if average >= 80:

            strong.append(topic)



        elif average < 60:

            weak.append(topic)



    total_time = sum(
        topic_times.values()
    )



    return strong, weak, total_time






def create_student_insight(logs):


    strong, weak, total = analyze_study(
        logs
    )


    if len(weak) >= 3:


        risk = "high"


        recommendation = (

            "Birden fazla zayıf konu var. "
            "Tekrar planı oluşturulmalı."

        )


    elif len(weak) > 0:


        risk = "medium"


        recommendation = (

            "Zayıf konulara ek çalışma yapılmalı."

        )


    else:


        risk = "low"


        recommendation = (

            "Mevcut çalışma düzeni devam etmeli."

        )



    return StudentInsight(

        strong_topics=strong,

        weak_topics=weak,

        total_study_time=total,

        risk_level=risk,

        recommendation=recommendation

    )