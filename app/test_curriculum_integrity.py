from curriculum_engine import load_curriculum_data


REQUIRED_FIELDS = {
    "subject",
    "exam",
    "topic",
    "subtopics",
    "priority",
    "dependencies",
    "next_topics",
    "estimated_hours",
    "difficulty",
    "question_weight",
}


def load_all():
    return load_curriculum_data()


def normalize_reference(reference):
    """
    Cross-exam references can be written like:

    TYT Hücre
    AYT Fonksiyonlar

    References without an exam prefix stay
    in the current exam.
    """

    if reference.startswith("TYT "):
        return "TYT", reference[4:]

    if reference.startswith("AYT "):
        return "AYT", reference[4:]

    return None, reference


def build_topic_index(curriculum):

    index = set()

    for item in curriculum:

        index.add(
            (
                item["exam"],
                item["subject"],
                item["topic"],
            )
        )

    return index


def resolve_reference(item, reference):

    reference_exam, reference_topic = normalize_reference(
        reference
    )

    exam = reference_exam or item["exam"]

    return (
        exam,
        item["subject"],
        reference_topic,
    )


def test_curriculum_total_record_count():

    curriculum = load_all()

    assert len(curriculum) == 165


def test_all_curriculum_records_have_required_fields():

    curriculum = load_all()

    for item in curriculum:

        missing = REQUIRED_FIELDS - set(item.keys())

        assert not missing, (
            f"{item.get('exam')} / "
            f"{item.get('subject')} / "
            f"{item.get('topic')} "
            f"missing fields: {missing}"
        )


def test_curriculum_field_types():

    curriculum = load_all()

    for item in curriculum:

        assert isinstance(item["subject"], str)
        assert isinstance(item["exam"], str)
        assert isinstance(item["topic"], str)

        assert isinstance(item["subtopics"], list)
        assert isinstance(item["dependencies"], list)
        assert isinstance(item["next_topics"], list)

        assert isinstance(
            item["estimated_hours"],
            (int, float),
        )

        assert item["estimated_hours"] > 0

        assert item["exam"] in {
            "TYT",
            "AYT",
        }

        assert item["priority"] in {
            "low",
            "medium",
            "high",
            "critical",
        }

        assert item["difficulty"] in {
            "easy",
            "medium",
            "hard",
        }

        assert item["question_weight"] in {
            "low",
            "medium",
            "high",
            "very_high",
        }


def test_no_duplicate_curriculum_topics():

    curriculum = load_all()

    seen = set()

    for item in curriculum:

        key = (
            item["exam"],
            item["subject"],
            item["topic"],
        )

        assert key not in seen, (
            f"Duplicate curriculum topic: {key}"
        )

        seen.add(key)


def test_topics_have_subtopics():

    curriculum = load_all()

    for item in curriculum:

        assert len(item["subtopics"]) > 0, (
            f"No subtopics: "
            f"{item['exam']} / "
            f"{item['subject']} / "
            f"{item['topic']}"
        )


def test_no_duplicate_subtopics_inside_topic():

    curriculum = load_all()

    for item in curriculum:

        subtopics = item["subtopics"]

        assert len(subtopics) == len(set(subtopics)), (
            f"Duplicate subtopic: "
            f"{item['exam']} / "
            f"{item['subject']} / "
            f"{item['topic']}"
        )


def test_dependencies_do_not_point_to_self():

    curriculum = load_all()

    for item in curriculum:

        for dependency in item["dependencies"]:

            dependency_exam, dependency_topic = (
                normalize_reference(dependency)
            )

            same_exam = (
                dependency_exam is None
                or dependency_exam == item["exam"]
            )

            assert not (
                same_exam
                and dependency_topic == item["topic"]
            ), (
                f"Self dependency: "
                f"{item['exam']} / "
                f"{item['subject']} / "
                f"{item['topic']}"
            )


def test_next_topics_do_not_point_to_self():

    curriculum = load_all()

    for item in curriculum:

        for next_topic in item["next_topics"]:

            next_exam, next_topic_name = (
                normalize_reference(next_topic)
            )

            same_exam = (
                next_exam is None
                or next_exam == item["exam"]
            )

            assert not (
                same_exam
                and next_topic_name == item["topic"]
            ), (
                f"Self next_topic: "
                f"{item['exam']} / "
                f"{item['subject']} / "
                f"{item['topic']}"
            )


def test_all_topics_have_valid_identity():

    curriculum = load_all()

    for item in curriculum:

        assert item["subject"].strip()
        assert item["topic"].strip()

        for subtopic in item["subtopics"]:

            assert isinstance(subtopic, str)
            assert subtopic.strip()

        for dependency in item["dependencies"]:

            assert isinstance(dependency, str)
            assert dependency.strip()

        for next_topic in item["next_topics"]:

            assert isinstance(next_topic, str)
            assert next_topic.strip()


def test_all_dependencies_reference_existing_topics():

    curriculum = load_all()

    index = build_topic_index(
        curriculum
    )

    missing = []

    for item in curriculum:

        for dependency in item["dependencies"]:

            target = resolve_reference(
                item,
                dependency,
            )

            if target not in index:

                missing.append(
                    (
                        item["exam"],
                        item["subject"],
                        item["topic"],
                        dependency,
                    )
                )

    assert not missing, (
        "Missing curriculum dependencies:\n"
        + "\n".join(
            str(item)
            for item in missing
        )
    )


def test_all_next_topics_reference_existing_topics():

    curriculum = load_all()

    index = build_topic_index(
        curriculum
    )

    missing = []

    for item in curriculum:

        for next_topic in item["next_topics"]:

            target = resolve_reference(
                item,
                next_topic,
            )

            if target not in index:

                missing.append(
                    (
                        item["exam"],
                        item["subject"],
                        item["topic"],
                        next_topic,
                    )
                )

    assert not missing, (
        "Missing curriculum next_topics:\n"
        + "\n".join(
            str(item)
            for item in missing
        )
    )