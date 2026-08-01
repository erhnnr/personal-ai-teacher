from subjects import SUBJECT_KEYWORDS


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


def detect_subject(question: str):

    if not question:
        return None

    text = normalize_text(question)

    for subject, keywords in SUBJECT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                return subject

    return None