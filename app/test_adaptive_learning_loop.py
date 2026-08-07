from adaptive_learning_loop import process_learning_result



def test_learning_loop_weak_student():

    result = process_learning_result(

        "AYT",

        "Matematik",

        "Limit",

        40

    )


    assert result["next_action"] == "review"

    assert result["recommended_topic"] == "Fonksiyonlar"



def test_learning_loop_success_student():

    result = process_learning_result(

        "AYT",

        "Matematik",

        "Limit",

        95

    )


    assert result["next_action"] == "advance"

    assert result["recommended_topic"] == "Türev"