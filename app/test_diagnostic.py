from diagnostic import update_diagnostic, get_student_diagnostic



def test_diagnostic():


    update_diagnostic({

        "math": 80,

        "turkish": 75,

        "science": 60,

        "problem_solving": 55,


        "topics": {

            "Fonksiyonlar": 50,

            "Sayılar": 90,

            "Problemler": 45

        }

    })


    data = get_student_diagnostic()


    assert data["math"] == 80

    assert data["level"] == "intermediate"


    assert "Fonksiyonlar" in data["weak_topics"]

    assert "Sayılar" in data["strong_topics"]

    assert data["completed"] == True