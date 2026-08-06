from pathlib import Path
import json
import sys


REQUIRED_FILES = [
    "concept.json",
    "examples.json",
    "mistakes.json",
    "relations.json"
]


def validate_topic(path):

    topic_path = Path(path)

    if not topic_path.exists():
        print("ERROR: Topic path does not exist")
        return False

    success = True

    for filename in REQUIRED_FILES:

        file_path = topic_path / filename

        if not file_path.exists():
            print(f"Missing file: {filename}")
            success = False
            continue

        try:
            json.loads(
                file_path.read_text(
                    encoding="utf-8"
                )
            )

            print(f"OK: {filename}")

        except json.JSONDecodeError:
            print(f"INVALID JSON: {filename}")
            success = False


    if success:
        print("\nKnowledge package is valid")
    else:
        print("\nKnowledge package validation failed")

    return success


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python validate_knowledge.py <topic_path>"
        )
        sys.exit(1)

    result = validate_topic(sys.argv[1])

    if not result:
        sys.exit(1)