"""
EIE-010 LessonPlan

Purpose:
Common data model for lesson planning.
"""

from dataclasses import dataclass


@dataclass
class LessonPlan:

    student: object

    subject: str

    grade: str

    topics: list[str]

    question: str

    topic: str = ""

    goal: str = ""

    allowed: bool = True

    reason: str = ""

    next_topic: str = ""