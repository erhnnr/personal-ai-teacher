import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "student_profile.json"


class Student:

    def __init__(self):

        self.name = ""
        self.grade = 9
        self.goal = "TYT"

        self.level = "beginner"

        self.learning_style = "normal"

        self.current_subject = ""

        self.current_topic = ""

        self.weak_topics = []

        self.strong_topics = []

        self.completed_topics = []

    def to_dict(self):

        return {
            "name": self.name,
            "grade": self.grade,
            "goal": self.goal,
            "level": self.level,
            "learning_style": self.learning_style,
            "current_subject": self.current_subject,
            "current_topic": self.current_topic,
            "weak_topics": self.weak_topics,
            "strong_topics": self.strong_topics,
            "completed_topics": self.completed_topics
        }


def save_student(student):

    with open(DATA_FILE, "w", encoding="utf8") as f:

        json.dump(student.to_dict(), f, ensure_ascii=False, indent=4)


def load_student():

    if not DATA_FILE.exists():

        student = Student()

        save_student(student)

        return student

    with open(DATA_FILE, "r", encoding="utf8") as f:

        data = json.load(f)

    student = Student()

    student.__dict__.update(data)

    return student