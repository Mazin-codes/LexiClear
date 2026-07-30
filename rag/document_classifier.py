from rag.providers.llm_factory import generate

DOCUMENT_TYPES = [
    "employment_contract",
    "rental_agreement",
    "nda",
    "service_agreement",
    "consumer_notice",
    "court_order",
    "legal_notice",
    "property_sale",
    "will",
    "power_of_attorney",
    "privacy_policy",
    "terms_and_conditions",
    "other"
]


def classify_document(documents):

    text = "\n".join(
        page.page_content
        for page in documents[:3]
    )

    prompt = f"""
You are an expert legal document classifier.

Identify ONLY the document type.

Choose exactly ONE from:

{", ".join(DOCUMENT_TYPES)}

Document:

{text}

Return ONLY the document type.
"""

    prediction = generate(prompt).strip().lower()

    if prediction not in DOCUMENT_TYPES:
        prediction = "other"

    return prediction