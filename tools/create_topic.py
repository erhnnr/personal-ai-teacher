from pathlib import Path
import json
import sys


BASE_PATH = Path("data/knowledge/units")


def create_topic(subject, grade, topic):
    topic_path = BASE_PATH / subject / grade / topic

    topic_path.mkdir(parents=True, exist_ok=True)

    files = {
        "concept.json": {
            "topic": topic,
            "subject": subject,
            "grade": grade,
            "concepts": []
        },
        "examples.json": {
            "examples": []
        },
        "mistakes.json": {
            "common_mistakes": []
        },
        "relations.json": {
            "relations": []
        }
    }

    for filename, content in files.items():
        file_path = topic_path / filename

        if not file_path.exists():
            file_path.write_text(
                json.dumps(
                    content,
                    indent=4,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

    print(f"Knowledge package created:")
    print(topic_path)


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print(
            "Usage: python create_topic.py <subject> <grade> <topic>"
        )
        sys.exit(1)

    create_topic(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3]
    )