from adaptive_curriculum import decide_next_action



def test_weak_student_reviews_dependency():

    result = decide_next_action(

        "AYT",

        "Matematik",

        "Limit",

        45

    )


    assert result["action"] == "review"

    assert result["topic"] == "Fonksiyonlar"



def test_good_student_advances():

    result = decide_next_action(

        "AYT",

        "Matematik",

        "Limit",

        90

    )


    assert result["action"] == "advance"

    assert result["topic"] == "Türev"