from groq import Groq
from dotenv import load_dotenv
import os
from rag.providers.llm_factory import generate

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def analyze_risks(docs):

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    # Limit context size to prevent exceeding API limits
    context = context[:15000]

    prompt = f"""
You are an expert Legal Risk Assessment AI.

Analyze ONLY the retrieved document.

Retrieved Context:
{context}

Your task is to identify every legal or contractual risk.

For each risk provide:

1. Risk Category
Choose ONLY one:
- Contract Termination
- Payment Obligation
- Financial Penalty
- Legal Liability
- Confidentiality
- Privacy
- Compliance
- Intellectual Property
- Deadline
- Renewal / Expiry
- Other

2. Risk Level
Choose ONLY one:
- High
- Medium
- Low

3. Relevant Clause
Quote the important sentence.

4. Explanation
Explain in simple English why this is a risk.

5. Possible Impact
Explain what may happen if ignored.

6. Recommendation
Suggest what the user should do.

If there are NO risks, reply exactly:

No significant legal risks detected.

Return the answer neatly using markdown headings.
"""

    return generate(prompt)