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


_KEYWORD_HINTS = {
    "employment_contract": [
        "employment agreement", "employment contract",
        "employer", "employee", "probationary period",
        "designation", "salary", "compensation",
        "termination of employment", "notice period",
    ],
    "rental_agreement": [
        "rental agreement", "lease agreement", "rent",
        "landlord", "tenant", "lease term", "security deposit",
        "premises", "monthly rent",
    ],
    "nda": [
        "non-disclosure", "confidentiality agreement",
        "nda", "confidential information",
    ],
}


def _keyword_preclassify(text: str) -> str | None:
    """Fast keyword scan — returns a type if one category clearly dominates."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for doc_type, keywords in _KEYWORD_HINTS.items():
        scores[doc_type] = sum(1 for kw in keywords if kw in text_lower)

    if not scores:
        return None

    best = max(scores, key=scores.get)
    runner_up = sorted(scores.values(), reverse=True)

    # Only trust the keyword check if the best score is ≥ 3 hits
    # and clearly ahead of the runner-up
    if scores[best] >= 3 and (len(runner_up) < 2 or scores[best] > runner_up[1] + 1):
        return best

    return None


def classify_document(documents):

    text = "\n".join(
        page.page_content
        for page in documents[:3]
    )

    # Fast keyword-based pre-check
    keyword_result = _keyword_preclassify(text)
    if keyword_result:
        return keyword_result

    prompt = f"""
You are an expert legal document classifier.

Identify ONLY the document type from the text below.

IMPORTANT DISTINCTIONS:
- "employment_contract" → relates to hiring, salary, designation, employer/employee
- "rental_agreement" → relates to renting property, landlord/tenant, lease, monthly rent

Choose exactly ONE from:

{", ".join(DOCUMENT_TYPES)}

Document:

{text}

Return ONLY the document type label, nothing else.
"""

    prediction = generate(prompt).strip().lower().replace('"', '').replace("'", "")

    # Clean up common LLM formatting artifacts
    for dt in DOCUMENT_TYPES:
        if dt in prediction:
            return dt

    if prediction not in DOCUMENT_TYPES:
        prediction = "other"

    return prediction