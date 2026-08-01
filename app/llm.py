"""
Module:
LLM Client

Purpose:
Create the OpenAI client used by the application.
"""

from openai import OpenAI
from config import LM_STUDIO_URL

client = OpenAI(
    base_url=LM_STUDIO_URL,
    api_key="lm-studio"
)