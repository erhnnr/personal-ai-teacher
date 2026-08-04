"""
EIE-040 Diagnostic Engine

Purpose:
Measure and analyze student skill levels.
"""


from student import load_student, save_student



def calculate_level(score):

    if score >= 85:
        return "advanced"

    elif score >= 65:
        return "intermediate"

    elif score >= 40:
        return "basic"

    else:
        return "beginner"



def analyze_topics(topic_scores):

    weak_topics = []

    strong_topics = []


    for topic, score in topic_scores.items():

        if score < 60:

            weak_topics.append(topic)


        elif score >= 85:

            strong_topics.append(topic)



    return weak_topics, strong_topics



def update_diagnostic(results):

    student = load_student()


    if "math" in results:

        student.math_level = results["math"]


    if "turkish" in results:

        student.turkish_level = results["turkish"]


    if "science" in results:

        student.science_level = results["science"]


    if "problem_solving" in results:

        student.problem_solving_level = results["problem_solving"]



    scores = [

        value for key, value in results.items()

        if isinstance(value, (int, float))

    ]


    if scores:

        average = sum(scores) / len(scores)

        student.level = calculate_level(
            average
        )



    if "topics" in results:

        weak, strong = analyze_topics(
            results["topics"]
        )

        student.weak_topics = weak

        student.strong_topics = strong



    student.assessment_completed = True


    save_student(student)


    return student



def get_student_diagnostic():

    student = load_student()


    return {

        "math": student.math_level,

        "turkish": student.turkish_level,

        "science": student.science_level,

        "problem_solving": student.problem_solving_level,

        "weak_topics": student.weak_topics,

        "strong_topics": student.strong_topics,

        "level": student.level,

        "completed": student.assessment_completed

    }
def check_topic_readiness(topic):

    student = load_student()


    prerequisites = {

        "Limit": [
            "Fonksiyonlar",
            "Denklemler"
        ],

        "Türev": [
            "Limit"
        ],

        "İntegral": [
            "Türev"
        ]
    }


    if topic not in prerequisites:

        return {
            "ready": True,
            "missing": []
        }


    missing = []


    for item in prerequisites[topic]:

        if item in student.weak_topics:

            missing.append(item)



    return {

        "ready": len(missing) == 0,

        "missing": missing

    }