"""
Module:
LLM Client

Purpose:
Create and configure the OpenAI-compatible
client used to communicate with LM Studio.
"""

from openai import OpenAI

from config import (
    LM_STUDIO_URL,
    LLM_TIMEOUT,
)


client = OpenAI(
    base_url=LM_STUDIO_URL,
    api_key="lm-studio",
    timeout=LLM_TIMEOUT,
)


def get_available_models():
    """
    Return model identifiers currently visible
    through the LM Studio server.
    """

    models = client.models.list()

    return [
        model.id
        for model in models.data
    ]


def check_llm_connection():
    """
    Check whether LM Studio is reachable.

    Returns a dictionary instead of crashing
    the application.
    """

    try:

        models = get_available_models()

        return {
            "connected": True,
            "models": models,
            "error": None,
        }

    except Exception as exc:

        return {
            "connected": False,
            "models": [],
            "error": str(exc),
        }