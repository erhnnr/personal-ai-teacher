"""
EIE-007 Memory Engine

Purpose:
Manage student memory.
"""

import json
from pathlib import Path

MEMORY_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "runtime"
    / "memory.json"
)

DEFAULT_MEMORY = {
    "last_topic": "",
    "completed_topics": [],
    "weak_topics": [],
    "study_history": [],
    "quiz_history": [],
    "last_study_date": ""
}


def load_memory():
    """
    Load memory from disk.
    If the file does not exist, create it automatically.
    """

    if not MEMORY_FILE.exists():
        clear_memory()

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    """
    Save memory to disk.
    """

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4, ensure_ascii=False)


def get_last_topic():
    return load_memory()["last_topic"]


def set_last_topic(topic):
    memory = load_memory()
    memory["last_topic"] = topic
    save_memory(memory)


def add_completed_topic(topic):
    memory = load_memory()

    if topic not in memory["completed_topics"]:
        memory["completed_topics"].append(topic)

    save_memory(memory)


def add_weak_topic(topic):
    memory = load_memory()

    if topic not in memory["weak_topics"]:
        memory["weak_topics"].append(topic)

    save_memory(memory)


def add_study_history(record):
    memory = load_memory()
    memory["study_history"].append(record)
    save_memory(memory)


def add_quiz_result(record):
    memory = load_memory()
    memory["quiz_history"].append(record)
    save_memory(memory)


def clear_memory():
    """
    Reset memory to default state.
    """
    save_memory(DEFAULT_MEMORY.copy())