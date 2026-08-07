from student_session import start_session



def test_student_session():

    session = start_session(
        "Matematik",
        12,
        "Limit"
    )


    assert session is not None

    assert session["topic"] == "Limit"

    assert len(session["questions"]) > 0