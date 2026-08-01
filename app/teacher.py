"""
Module:
EIE-009 Teacher Engine

Purpose:
Communicate with the LLM using Prompt Builder.
"""

from llm import client
from config import MODEL_NAME

from planner import create_plan
from prompt_builder import build_prompt


def ask_teacher(question):

    plan = create_plan(question)

    prompt = build_prompt(question, plan)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content