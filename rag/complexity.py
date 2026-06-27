import re

LEGAL_TERMS = [
    "agreement",
    "liability",
    "indemnify",
    "termination",
    "confidential",
    "penalty",
    "breach",
    "obligation",
    "compliance",
    "arbitration",
    "damages",
    "claim",
    "contract",
    "notice"
]

def analyze_document_complexity(documents):

    text = "\n".join(
        [doc.page_content for doc in documents]
    )

    words = text.split()
    total_words = len(words)

    sentences = re.split(r'[.!?]+', text)

    sentences = [
        s.strip()
        for s in sentences
        if s.strip()
    ]

    total_sentences = max(len(sentences), 1)

    avg_sentence_length = (
        total_words / total_sentences
    )

    legal_term_count = sum(
        text.lower().count(term)
        for term in LEGAL_TERMS
    )

    reading_time = round(
        total_words / 200,
        1
    )

    score = 0

    score += min(
        avg_sentence_length * 2,
        40
    )

    score += min(
        legal_term_count,
        30
    )

    score += min(
        total_words / 100,
        30
    )

    score = round(
        min(score, 100)
    )

    if score <= 30:
        level = "Easy"
    elif score <= 60:
        level = "Moderate"
    else:
        level = "Difficult"

    return {
        "score": score,
        "level": level,
        "words": total_words,
        "reading_time": reading_time,
        "avg_sentence_length": round(
            avg_sentence_length, 1
        ),
        "legal_terms": legal_term_count
    }