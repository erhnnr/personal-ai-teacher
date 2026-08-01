from topics import CURRICULUM


def normalize_text(text: str):

    replacements = {
        "İ": "i",
        "I": "i",
        "Ç": "c",
        "Ş": "s",
        "Ğ": "g",
        "Ü": "u",
        "Ö": "o",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.lower()


def detect_topic(question):

    if not question:
        return {
            "subject": None,
            "topic": None,
            "grade": None
        }

    question = normalize_text(question)

    for subject in CURRICULUM:

        for grade in CURRICULUM[subject]:

            for topic in CURRICULUM[subject][grade]:

                if normalize_text(topic) in question:

                    return {
                        "subject": subject,
                        "topic": topic,
                        "grade": grade
                    }

    return {
        "subject": None,
        "topic": None,
        "grade": None
    }