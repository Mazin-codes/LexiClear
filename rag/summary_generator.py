from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_document_summary(documents):

    text = "\n\n".join(
        [doc.page_content for doc in documents]
    )

    prompt = f"""
You are LexiClear+, an expert legal document analyst.

Analyze the document below and generate a structured summary.

Document:
{text[:12000]}

Return ONLY in the following format:

# Document Type

# Parties Involved

# Key Obligations
- item

# Important Dates
- item

# Financial Terms
- item

# Termination Conditions
- item

# Major Risks
- item

# Executive Summary
(5-10 line summary in simple English)

If information is not available, write:
"Not explicitly mentioned".
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert legal analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    return response.choices[0].message.content