from pathlib import Path
import json
import sys


def check_relations(topic_path):

    topic_path = Path(topic_path)

    relations_file = topic_path / "relations.json"

    if not relations_file.exists():
        print("ERROR: relations.json not found")
        return False

    try:
        data = json.loads(
            relations_file.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError:
        print("ERROR: Invalid JSON")
        return False


    relations = data.get("relations", [])

    if not isinstance(relations, list):
        print("ERROR: relations must be a list")
        return False


    valid = True

    for index, relation in enumerate(relations):

        if not isinstance(relation, dict):
            print(
                f"ERROR: Relation {index} is not an object"
            )
            valid = False
            continue

        if "from" not in relation or "to" not in relation:
            print(
                f"ERROR: Relation {index} missing from/to"
            )
            valid = False


    if valid:
        print("Relations are valid")
    else:
        print("Relation validation failed")


    return valid



if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python check_links.py <topic_path>"
        )
        sys.exit(1)


    result = check_relations(sys.argv[1])

    if not result:
        sys.exit(1)