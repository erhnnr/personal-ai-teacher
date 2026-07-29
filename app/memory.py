import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_student_profile():
    file = DATA_DIR / "student_profile.json"

    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_progress():
    file = DATA_DIR / "progress.json"

    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress):
    file = DATA_DIR / "progress.json"

    with open(file, "w", encoding="utf-8") as f:
        json.dump(
            progress,
            f,
            ensure_ascii=False,
            indent=2
        )