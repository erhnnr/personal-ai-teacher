"""
EIE-030 Quiz LLM Adapter

Purpose:
Generate quiz content using LLM.
"""


from llm import client
from config import MODEL_NAME
from quiz_prompts import quiz_generator_prompt



def generate_question(topic):

    prompt = quiz_generator_prompt()


    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[

            {
                "role": "system",
                "content": prompt
            },

            {
                "role": "user",
                "content": f"{topic} konusu için bir soru üret."
            }

        ],

        temperature=0.7

    )


    return response.choices[0].message.content