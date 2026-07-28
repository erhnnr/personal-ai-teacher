from openai import OpenAI
from config import LM_STUDIO_URL, MODEL_NAME


client = OpenAI(
    base_url=LM_STUDIO_URL,
    api_key="lm-studio"
)


def ask_teacher(question):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": """
Sen kişisel TYT ve AYT yapay zeka öğretmenisin.

Kurallar:
- Öğrencinin seviyesine göre anlat.
- Önce temel mantığı açıkla.
- Örnek ver.
- Gerektiğinde soru sor.
"""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content