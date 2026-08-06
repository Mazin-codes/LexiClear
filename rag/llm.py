from dotenv import load_dotenv
from rag.citations import format_legal_sources
from rag.providers.llm_factory import generate

load_dotenv()


def generate_answer(question, context, language="English"):

    document_context = context["document_context"]
    legal_context = context["legal_context"]

    prompt = f"""
You are LexiClear+, an AI legal assistant specialized in simplifying legal documents.

You have TWO knowledge sources.

========================================================
UPLOADED DOCUMENT
========================================================

{document_context}

========================================================
LEGAL REFERENCE CORPUS
========================================================

{legal_context}

========================================================
QUESTION
========================================================

{question}

Instructions:

1. Answer using the uploaded document FIRST.
2. Use the legal corpus only to explain, validate, or provide legal context.
3. Never contradict the uploaded document.
4. If the uploaded document conflicts with general legal guidance,
   clearly mention the difference.
5. If the document does not contain the requested information,
   explicitly say so.
6. Do not invent clauses.
7. Answer entirely in {language}, using clear, plain language appropriate for a
   non-lawyer. Keep all clause numbers, section references, case citations, statute
   names, dates, monetary amounts, percentages, and quoted legal text exactly as they
   appear in the sources.
8. The headings below must also be in {language}; do not translate legal citations.

Return the answer in these five sections, translating each section heading into
{language}:

## Direct Answer

(Answer the user's question.)

---

## What the Document Says

(Quote or summarize the relevant clause.)

---

## Legal Perspective

(Explain the applicable law or legal guidance from the legal corpus.
If none is available, write "No relevant legal reference found.")

---

## Practical Meaning

(Explain what this means for a normal person.)

---

## Recommendation

(Explain what the user should keep in mind before acting.)
"""

    answer = generate(prompt)
    return answer + format_legal_sources(context.get("legal_chunks", []))
