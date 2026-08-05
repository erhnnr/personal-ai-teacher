"""
EIE-041 Student Model

Purpose:
Store complete student profile.
"""


import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "student"
    / "student_profile.json"
)



class Student:


    def __init__(self):

        # Temel bilgiler

        self.name = ""

        self.grade = 12


        # Sınav bilgileri

        self.exam = "YKS"

        self.target_year = 2027

        self.goal = "TYT + AYT"


        # Alan

        self.field = "Sayısal"


        # Kariyer hedefi

        self.career_goal = [

            "Tıp",

            "Mühendislik"

        ]


        # Genel seviye

        self.level = "beginner"


        self.learning_style = "normal"



        # Ders seviyeleri

        self.math_level = 0

        self.physics_level = 0

        self.chemistry_level = 0

        self.biology_level = 0

        self.turkish_level = 0



        # Konu takibi


        self.current_subject = ""

        self.current_topic = ""


        self.weak_topics = []


        self.strong_topics = []


        self.completed_topics = []



        # Sistem durumu


        self.assessment_completed = False


        self.daily_study_time = 0



    def to_dict(self):

        return self.__dict__



def save_student(student):

    with open(

        DATA_FILE,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            student.to_dict(),

            f,

            ensure_ascii=False,

            indent=4

        )




def load_student():


    if not DATA_FILE.exists():


        student = Student()

        save_student(student)

        return student



    with open(

        DATA_FILE,

        "r",

        encoding="utf-8"

    ) as f:


        data = json.load(f)



    student = Student()


    student.__dict__.update(data)


    return student