from learning_intelligence_engine import (
    decide_learning_action
)



def test_review_decision():

    result = decide_learning_action(
        "AYT",
        "Matematik",
        "Limit",
        45,
        2
    )


    assert result["decision"] == "review"



def test_advance_decision():

    result = decide_learning_action(
        "AYT",
        "Matematik",
        "Limit",
        95,
        3
    )


    assert result["decision"] == "advance"

    assert result["target"] == "Türev"