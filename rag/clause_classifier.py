import re

CATEGORIES = {
    "Termination": [
        "terminate",
        "termination",
        "cancel",
        "end agreement"
    ],

    "Payment": [
        "payment",
        "salary",
        "fee",
        "invoice",
        "amount payable"
    ],

    "Confidentiality": [
        "confidential",
        "non-disclosure",
        "privacy"
    ],

    "Liability": [
        "liable",
        "liability",
        "damages",
        "indemnify"
    ],

    "Deadline": [
        "within",
        "days",
        "deadline",
        "notice period"
    ],

    "Compliance": [
        "comply",
        "compliance",
        "regulation",
        "law"
    ]
}


def classify_clauses(docs):

    text = "\n".join(
        [doc.page_content for doc in docs]
    )

    sentences = re.split(
        r'[.!?]+',
        text
    )

    results = {}

    for category in CATEGORIES:
        results[category] = []

    for sentence in sentences:

        s = sentence.strip()

        if len(s) < 20:
            continue

        lower = s.lower()

        for category, keywords in CATEGORIES.items():

            if any(
                keyword in lower
                for keyword in keywords
            ):

                results[category].append(s)

    return results