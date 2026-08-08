"""
Knowledge Package Validator

Purpose:
Determine whether a knowledge topic contains
enough structured and consistent educational
content to be considered READY.

READY means:
- all required files exist,
- all files contain valid JSON,
- topic identity is consistent,
- concept data is complete,
- at least one definition exists,
- at least one rule exists,
- at least one example exists,
- at least one documented mistake exists,
- relation structures are valid.

This validator checks structural readiness.
It does not claim that the educational content
is factually correct merely because the structure
passes validation.
"""

from pathlib import Path
import json
import sys


REQUIRED_FILES = (
    "concept.json",
    "examples.json",
    "mistakes.json",
    "relations.json",
)


def load_json(
    file_path,
    errors,
):
    """
    Safely load one JSON file.
    """

    if not file_path.exists():

        errors.append(
            f"Missing file: {file_path.name}"
        )

        return None

    try:

        return json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:

        errors.append(
            f"Invalid JSON in "
            f"{file_path.name}: {exc}"
        )

        return None


def non_empty_string(value):
    return (
        isinstance(value, str)
        and bool(value.strip())
    )


def non_empty_string_list(value):
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(
            non_empty_string(item)
            for item in value
        )
    )


def validate_concept(
    concept,
    errors,
):
    """
    Validate canonical concept.json.
    """

    if not isinstance(
        concept,
        dict,
    ):

        errors.append(
            "concept.json must contain an object"
        )

        return

    required_strings = (
        "id",
        "subject",
        "grade",
        "topic",
    )

    for field in required_strings:

        if not non_empty_string(
            concept.get(field)
        ):

            errors.append(
                f"concept.{field} must be "
                "a non-empty string"
            )

    grade = str(
        concept.get(
            "grade",
            "",
        )
    )

    if grade and not grade.isdigit():

        errors.append(
            "concept.grade must contain "
            "only digits"
        )

    if not non_empty_string_list(
        concept.get(
            "learning_objectives"
        )
    ):

        errors.append(
            "concept.learning_objectives "
            "must contain at least one item"
        )

    prerequisites = concept.get(
        "prerequisites"
    )

    if not isinstance(
        prerequisites,
        list,
    ):

        errors.append(
            "concept.prerequisites "
            "must be a list"
        )

    elif not all(
        non_empty_string(item)
        for item in prerequisites
    ):

        errors.append(
            "concept.prerequisites contains "
            "an invalid item"
        )

    if not non_empty_string_list(
        concept.get(
            "core_concepts"
        )
    ):

        errors.append(
            "concept.core_concepts must "
            "contain at least one item"
        )

    definitions = concept.get(
        "definitions"
    )

    if (
        not isinstance(
            definitions,
            list,
        )
        or not definitions
    ):

        errors.append(
            "concept.definitions must "
            "contain at least one definition"
        )

    else:

        for index, definition in enumerate(
            definitions
        ):

            if not isinstance(
                definition,
                dict,
            ):

                errors.append(
                    f"definition {index} "
                    "must be an object"
                )

                continue

            if not non_empty_string(
                definition.get(
                    "term"
                )
            ):

                errors.append(
                    f"definition {index} "
                    "is missing term"
                )

            if not non_empty_string(
                definition.get(
                    "definition"
                )
            ):

                errors.append(
                    f"definition {index} "
                    "is missing definition text"
                )

    if not non_empty_string_list(
        concept.get(
            "rules"
        )
    ):

        errors.append(
            "concept.rules must contain "
            "at least one rule"
        )

    for optional_list in (
        "common_confusions",
        "teaching_notes",
    ):

        value = concept.get(
            optional_list
        )

        if not isinstance(
            value,
            list,
        ):

            errors.append(
                f"concept.{optional_list} "
                "must be a list"
            )

        elif not all(
            non_empty_string(item)
            for item in value
        ):

            errors.append(
                f"concept.{optional_list} "
                "contains an invalid item"
            )


def validate_examples(
    examples,
    errors,
):
    """
    Validate examples.json.
    """

    if not isinstance(
        examples,
        dict,
    ):

        errors.append(
            "examples.json must contain an object"
        )

        return

    items = examples.get(
        "examples"
    )

    if (
        not isinstance(
            items,
            list,
        )
        or not items
    ):

        errors.append(
            "examples.examples must contain "
            "at least one example"
        )

        return

    required_fields = (
        "id",
        "level",
        "type",
        "question",
        "answer",
        "learning_point",
    )

    allowed_levels = {
        "basic",
        "intermediate",
        "advanced",
    }

    for index, example in enumerate(
        items
    ):

        if not isinstance(
            example,
            dict,
        ):

            errors.append(
                f"example {index} must be an object"
            )

            continue

        for field in required_fields:

            if not non_empty_string(
                example.get(
                    field
                )
            ):

                errors.append(
                    f"example {index} "
                    f"is missing {field}"
                )

        level = example.get(
            "level"
        )

        if (
            level
            and level not in allowed_levels
        ):

            errors.append(
                f"example {index} "
                "has invalid level"
            )


def validate_mistakes(
    mistakes,
    errors,
):
    """
    Validate mistakes.json.
    """

    if not isinstance(
        mistakes,
        dict,
    ):

        errors.append(
            "mistakes.json must contain an object"
        )

        return

    items = mistakes.get(
        "mistakes"
    )

    if (
        not isinstance(
            items,
            list,
        )
        or not items
    ):

        errors.append(
            "mistakes.mistakes must contain "
            "at least one documented mistake"
        )

        return

    required_fields = (
        "id",
        "error",
        "explanation",
        "teacher_action",
    )

    for index, mistake in enumerate(
        items
    ):

        if not isinstance(
            mistake,
            dict,
        ):

            errors.append(
                f"mistake {index} must be an object"
            )

            continue

        for field in required_fields:

            if not non_empty_string(
                mistake.get(
                    field
                )
            ):

                errors.append(
                    f"mistake {index} "
                    f"is missing {field}"
                )


def validate_relation_items(
    name,
    items,
    required_fields,
    errors,
):
    """
    Validate one relation list.
    """

    if not isinstance(
        items,
        list,
    ):

        errors.append(
            f"relations.{name} must be a list"
        )

        return

    for index, item in enumerate(
        items
    ):

        if not isinstance(
            item,
            dict,
        ):

            errors.append(
                f"{name} relation {index} "
                "must be an object"
            )

            continue

        for field in required_fields:

            if not non_empty_string(
                item.get(
                    field
                )
            ):

                errors.append(
                    f"{name} relation {index} "
                    f"is missing {field}"
                )


def validate_relations(
    relations,
    errors,
):
    """
    Validate relations.json.
    """

    if not isinstance(
        relations,
        dict,
    ):

        errors.append(
            "relations.json must contain an object"
        )

        return

    validate_relation_items(
        "prerequisites",
        relations.get(
            "prerequisites"
        ),
        (
            "topic",
            "reason",
        ),
        errors,
    )

    validate_relation_items(
        "next_topics",
        relations.get(
            "next_topics"
        ),
        (
            "topic",
            "reason",
        ),
        errors,
    )

    validate_relation_items(
        "related_topics",
        relations.get(
            "related_topics"
        ),
        (
            "topic",
            "relation",
        ),
        errors,
    )


def validate_topic(
    path,
    verbose=True,
):
    """
    Validate one complete topic package.

    Returns:
        True  -> READY
        False -> NOT_READY
    """

    topic_path = Path(
        path
    )

    errors = []

    if not topic_path.exists():

        errors.append(
            "Topic path does not exist"
        )

    if not topic_path.is_dir():

        errors.append(
            "Topic path is not a directory"
        )

    if errors:

        if verbose:

            for error in errors:
                print(
                    f"ERROR: {error}"
                )

            print(
                "\nSTATUS: NOT_READY"
            )

        return False

    loaded = {}

    for filename in REQUIRED_FILES:

        loaded[filename] = load_json(
            topic_path / filename,
            errors,
        )

    concept = loaded[
        "concept.json"
    ]

    examples = loaded[
        "examples.json"
    ]

    mistakes = loaded[
        "mistakes.json"
    ]

    relations = loaded[
        "relations.json"
    ]

    if concept is not None:
        validate_concept(
            concept,
            errors,
        )

    if examples is not None:
        validate_examples(
            examples,
            errors,
        )

    if mistakes is not None:
        validate_mistakes(
            mistakes,
            errors,
        )

    if relations is not None:
        validate_relations(
            relations,
            errors,
        )

    # Cross-file topic identity.

    if isinstance(
        concept,
        dict,
    ):

        canonical_topic = concept.get(
            "topic"
        )

        for filename, data in (
            (
                "examples.json",
                examples,
            ),
            (
                "mistakes.json",
                mistakes,
            ),
            (
                "relations.json",
                relations,
            ),
        ):

            if not isinstance(
                data,
                dict,
            ):
                continue

            if (
                data.get("topic")
                != canonical_topic
            ):

                errors.append(
                    f"{filename} topic does not "
                    "match concept.json topic"
                )

    success = (
        len(errors) == 0
    )

    if verbose:

        if success:

            print(
                "Knowledge package validation passed"
            )

            print(
                "STATUS: READY"
            )

        else:

            for error in errors:

                print(
                    f"ERROR: {error}"
                )

            print(
                "\nKnowledge package validation failed"
            )

            print(
                "STATUS: NOT_READY"
            )

    return success


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python validate_knowledge.py "
            "<topic_path>"
        )

        sys.exit(1)

    result = validate_topic(
        sys.argv[1]
    )

    if not result:
        sys.exit(1)