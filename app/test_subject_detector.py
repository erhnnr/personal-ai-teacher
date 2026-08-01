from subject_detector import detect_subject


def test_math():

    assert detect_subject(
        "Fonksiyonlar nedir?"
    ) == "Matematik"


def test_biology():

    assert detect_subject(
        "Fotosentezi anlat."
    ) == "Biyoloji"


def test_physics():

    assert detect_subject(
        "Elektrik nedir?"
    ) == "Fizik"


def test_chemistry():

    assert detect_subject(
        "Atom ve mol konusu"
    ) == "Kimya"


def test_case_insensitive():

    assert detect_subject(
        "LİMİT çalışalım"
    ) == "Matematik"


def test_unknown():

    assert detect_subject(
        "Bugün biraz ders çalışalım"
    ) is None