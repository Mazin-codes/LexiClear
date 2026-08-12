import json

from rag.providers.llm_factory import generate


def extract_rights(documents):
    """
    Extract legal rights together with clause, section and page references.
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

    json_schema = """
{
  "tenant": [
    {
      "right": "",
      "clause": "",
      "section": "",
      "page": 1
    }
  ],
  "landlord": [
    {
      "right": "",
      "clause": "",
      "section": "",
      "page": 1
    }
  ],
  "shared": [
    {
      "right": "",
      "clause": "",
      "section": "",
      "page": 1
    }
  ]
}
"""

    prompt = f"""
You are an expert legal analyst.

Analyze the uploaded legal document.

Extract ONLY legal rights that are explicitly granted.

Group them into:

- tenant
- landlord
- shared

For every right include:

- right
- clause
- section
- page

Rules

- Never invent rights.
- Never infer rights.
- Ignore obligations.
- Ignore recommendations.
- Ignore permissions unless they explicitly grant a legal right.
- Merge duplicates.
- Use simple English.
- Preserve clause numbers exactly.
- Preserve page numbers exactly.
- If section is unavailable use "".
- If clause is unavailable use "".

Return ONLY valid JSON.

JSON Schema:

{json_schema}

Document:

{document_text}
"""

    response = generate(prompt).strip()

    if response.startswith("```"):
        response = (
            response.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    try:
        return json.loads(response)

    except Exception as e:

        print("\n========== RIGHTS PARSE ERROR ==========")
        print(e)
        print(response)

        return {
            "tenant": [],
            "landlord": [],
            "shared": []
        }