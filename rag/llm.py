from groq import Groq
from dotenv import load_dotenv

import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_answer(context, question):

    prompt = f"""
You are LexiClear.

You are a legal document assistant.

Answer ONLY from the context.

Context:
{context}

Question:
{question}

Provide:
1. Simple Explanation
2. Important Clauses
3. Risks if present

Do not hallucinate.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content