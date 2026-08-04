"""
EIE-060 Adaptive Daily Planner

Purpose:
Create flexible daily study plans.
"""

from dataclasses import dataclass



@dataclass
class DailyTask:

    subject: str
    topic: str
    duration: int
    status: str = "planned"




@dataclass
class DailyPlan:

    date: str

    tasks: list

    total_minutes: int

    flexibility: str

    note: str





def create_daily_plan(student, strategy):


    tasks = []


    focus_subjects = strategy.focus_subjects



    if "Matematik" in focus_subjects:

        tasks.append(

            DailyTask(

                subject="Matematik",

                topic="Mevcut zayıf konular",

                duration=60

            )

        )



    if "Fizik" in focus_subjects:

        tasks.append(

            DailyTask(

                subject="Fizik",

                topic="Konu tekrarı",

                duration=40

            )

        )



    if "Kimya" in focus_subjects:

        tasks.append(

            DailyTask(

                subject="Kimya",

                topic="Konu tekrarı",

                duration=40

            )

        )



    total = sum(

        task.duration

        for task in tasks

    )



    return DailyPlan(

        date="today",

        tasks=tasks,

        total_minutes=total,

        flexibility="high",

        note=(

            "Plan öğrencinin gerçek çalışma "
            "durumuna göre değiştirilebilir."

        )

    )





def update_daily_plan(plan, completed_tasks):


    completed_topics = [

        item["topic"]

        for item in completed_tasks

    ]



    for task in plan.tasks:


        if task.topic in completed_topics:

            task.status = "completed"



    remaining = [

        task

        for task in plan.tasks

        if task.status != "completed"

    ]



    if remaining:


        plan.note = (

            "Tamamlanmayan görevler "
            "sonraki güne aktarılabilir."

        )


    else:


        plan.note = (

            "Günlük hedef tamamlandı."

        )


    return plan