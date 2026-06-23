from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_answer(question, docs):

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    prompt = f"""
You are LexiClear+, an AI assistant that simplifies legal and technical documents.

IMPORTANT RULES:
- Answer ONLY from the retrieved context.
- If the answer is not available in the context, reply:
  "The information is not available in the uploaded document."
- Do not make up information.
- Keep explanations simple and easy to understand.

Retrieved Context:
{context}

Question:
{question}

Return your answer in exactly this format:

## Simple Explanation
(Explain in simple English)

## Important Clauses
- Point 1
- Point 2
- Point 3

## Risks
- Mention possible risks.
- If no risks are found, write "No significant risks identified."

## Key Terms
- Mention important legal or technical terms from the retrieved context.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert Legal AI Assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content