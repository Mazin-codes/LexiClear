import json

from rag.providers.llm_factory import generate


def extract_obligations(documents):
    """
    Extract obligations together with clause, section and page references.
    """

    document_text = ""

    for doc in documents:

        page = doc.metadata.get("page", 0) + 1
        section = doc.metadata.get("section", "Unknown")

        document_text += f"""

==============================
PAGE {page}
SECTION: {section}
==============================

{doc.page_content}

"""

    prompt = f"""
You are an expert legal analyst.

Analyze the uploaded legal document.

Extract ONLY obligations that are explicitly written.

Group them into:

- tenant
- landlord
- shared

For every obligation include:

- obligation
- clause
- section
- page

Rules

- Never invent obligations.
- Never infer obligations.
- Ignore permissions.
- Ignore recommendations.
- Merge duplicates.
- Use simple English.
- Keep clause numbers exactly.
- Keep page numbers exactly.
- If clause number is unavailable use "".
- If section is unavailable use "".

Return ONLY a valid JSON object.

Do NOT return:

- explanations
- notes
- markdown
- ```json
- comments
- text before the JSON
- text after the JSON

The FIRST character of your response must be {{The LAST character of your response must be }}

JSON Schema:

{{
  "tenant": [
    {{
      "obligation": "",
      "clause": "",
      "section": "",
      "page": 1
    }}
  ],
  "landlord": [
    {{
      "obligation": "",
      "clause": "",
      "section": "",
      "page": 1
    }}
  ],
  "shared": [
    {{
      "obligation": "",
      "clause": "",
      "section": "",
      "page": 1
    }}
  ]
}}

Document:

{document_text}
"""

    response = generate(prompt).strip()

    # Remove Markdown code fences if the LLM returns them
    if response.startswith("```"):
        response = (
            response.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    try:
        return json.loads(response)

    except Exception as e:

        print("\n========== OBLIGATION PARSE ERROR ==========")
        print("Exception:", e)
        print("\nLLM Response:")
        print(response)
        print("===========================================\n")

        return {
            "tenant": [],
            "landlord": [],
            "shared": []
        }