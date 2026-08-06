from knowledge_engine import (
    get_learning_package,
    get_relations,
    get_mistakes,
    get_examples
)



def test_get_relations():

    data = get_relations(
        "Limit"
    )

    assert data is not None

    assert "prerequisites" in data



def test_get_mistakes():

    data = get_mistakes(
        "Limit"
    )

    assert data is not None

    assert "mistakes" in data



def test_get_examples():

    data = get_examples(
        "Limit"
    )

    assert data is not None

    assert "examples" in data



def test_learning_package():

    package = get_learning_package(
        "Matematik",
        12,
        "Limit"
    )

    assert package is not None

    assert package["concept"]["topic"] == "Limit"

    assert package["relations"] is not None