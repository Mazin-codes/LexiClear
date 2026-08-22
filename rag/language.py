"""Language helpers for LexiClear's supported Indian languages."""

from typing import Optional
import re

from rag.providers.llm_factory import generate

TRANSLATION_CACHE: dict[tuple[str, str], str] = {}
SUPPORTED_LANGUAGES = {
    "english": "English",
    "en": "English",
    "hindi": "Hindi",
    "hi": "Hindi",
    "kannada": "Kannada",
    "kn": "Kannada",
}

# Keeps each translation request comfortably below a typical model context limit,
# while allowing normal legal paragraphs to remain intact.
MAX_PARAGRAPH_CHARACTERS = 3_000
BLANK_PAGE_MARKER = "[Blank Page]"


def is_table_block(text: str) -> bool:
    """Recognize common table layouts retained by PDF text extraction."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False

    markdown_rows = sum("|" in line for line in lines)
    ascii_rows = sum(line.lstrip().startswith(("+", "|")) for line in lines)
    # Layout extraction generally separates PDF columns with two or more spaces.
    aligned_rows = sum(bool(re.search(r"\S\s{2,}\S", line)) for line in lines)
    return markdown_rows >= 2 or ascii_rows >= 2 or aligned_rows >= 2


def split_page_blocks(text: str) -> list[tuple[str, str]]:
    """Split a page into prose paragraphs and table blocks in source order."""
    raw_blocks = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    return [
        ("table" if is_table_block(block) else "paragraph", block)
        for block in raw_blocks
    ]


def is_blank_page(text: str) -> bool:
    """Return whether PDF extraction produced no visible content for a page."""
    return not text or not text.strip()


def split_page_paragraphs(text: str) -> list[str]:
    """Split page text into translatable paragraphs without losing their order.

    PDF extraction commonly uses blank lines for paragraph boundaries. A very long
    extracted paragraph is further split at line, sentence, or word boundaries so a
    single request cannot consume an excessive context window.
    """
    pieces = []

    for block_type, block in split_page_blocks(text):
        # Keep a table together so its cells cannot become detached from their row.
        # This prioritizes table fidelity over splitting a rare oversized table.
        if block_type == "table":
            pieces.append(block)
            continue

        paragraph = block
        remaining = paragraph
        while len(remaining) > MAX_PARAGRAPH_CHARACTERS:
            window = remaining[:MAX_PARAGRAPH_CHARACTERS]
            split_at = max(
                window.rfind("\n"),
                window.rfind(". "),
                window.rfind("; "),
                window.rfind(" "),
            )
            # Avoid creating a tiny prefix where no sensible boundary was found.
            if split_at < MAX_PARAGRAPH_CHARACTERS // 2:
                split_at = MAX_PARAGRAPH_CHARACTERS
            else:
                split_at += 1
            pieces.append(remaining[:split_at].strip())
            remaining = remaining[split_at:].strip()
        if remaining:
            pieces.append(remaining)

    return pieces


def detect_language(text: str) -> str:
    """Detect a supported language using its writing system when possible."""
    if any("\u0900" <= character <= "\u097f" for character in text):
        return "Hindi"
    if any("\u0c80" <= character <= "\u0cff" for character in text):
        return "Kannada"
    return "English"


def resolve_language(language: Optional[str], text: str = "") -> str:
    """Return an allowed display language or infer one from the supplied text."""
    if language:
        normalized = language.strip().lower()
        if normalized not in SUPPORTED_LANGUAGES:
            raise ValueError("Supported languages are English, Hindi, and Kannada.")
        return SUPPORTED_LANGUAGES[normalized]
    return detect_language(text)


def translate_question_for_retrieval(question: str, language: str) -> str:
    """
    Translate non-English legal questions into English
    while preserving retrieval-critical legal terms.
    """

    if language == "English":
        return question

    prompt = f"""
Translate this legal question from {language} into English ONLY for semantic retrieval.

Rules:
- Preserve person names exactly.
- Preserve company names exactly.
- Preserve statute names exactly.
- Preserve clause numbers.
- Preserve section numbers.
- Preserve article numbers.
- Preserve dates.
- Preserve money amounts.
- Preserve quoted legal terms.
- Do NOT explain.
- Return ONLY the translated English query.

Question:
{question}
"""

    return generate(prompt).strip()


def translate_document(documents, language: str) -> list[dict]:
    """Translate every page paragraph-by-paragraph, retaining legal references."""
    translations = []
    for index, document in enumerate(documents, start=1):
        page_number = document.metadata.get("page_label", index)
        if is_blank_page(document.page_content):
            translations.append({
    "page": page_number,
    "language": language,
    "translation": BLANK_PAGE_MARKER,
    "is_blank_page": True,
})
            continue
        if language == "English":
            translations.append({
    "page": page_number,
    "language": language,
    "translation": document.page_content,
    "is_blank_page": False,
})
            continue
        translated_paragraphs = []
        for paragraph_number, paragraph in enumerate(
            split_page_paragraphs(document.page_content), start=1
        ):
            is_table = is_table_block(paragraph)
            content_type = "table" if is_table else "paragraph"
            structure_rule = (
                "This is a table. Preserve every row, column, header, cell order, "
                "and empty cell. Return it as a table; use Markdown table syntax if "
                "the extracted layout is ambiguous. Do not merge or omit cells."
                if is_table
                else "This is prose. Preserve the heading and bullet/list structure within it."
            )
            # Skip OCR garbage or tiny fragments
            if not paragraph.strip():
                continue

            if len(paragraph.split()) < 3:
                translated_paragraphs.append(paragraph)
                continue
            prompt = f"""
You are an expert legal translator.

Translate the following English legal {content_type}
into {language}.

STRICT RULES

1. Translate ALL prose completely.
2. Never summarize.
3. Never omit text.
4. Preserve headings.
5. Preserve bullet lists.
6. Preserve paragraph order.
7. Preserve tables exactly.

DO NOT TRANSLATE

- Personal names
- Company names
- Email addresses
- URLs
- Phone numbers
- Property IDs
- Registration numbers
- Bank account numbers

LEGAL REFERENCES

Copy exactly:

- Clause numbers
- Section numbers
- Article numbers
- Schedule labels
- Dates
- Currency
- Percentages
- Case citations

Never translate official Act names, including:

- Indian Contract Act, 1872
- Transfer of Property Act, 1882
- Arbitration and Conciliation Act, 1996
- Information Technology Act, 2000
- Digital Personal Data Protection Act, 2023
- Consumer Protection Act, 2019


DEFINED LEGAL TERMS

Never translate these defined legal terms whenever they appear:

Lessor
Lessee
Agreement
Premises
Licensor
Licensee
Landlord
Tenant
Party
Parties

appear in quotation marks,
keep them in English.

Never translate:

- Signatures
- Witness names
- Initials
- Seal text

Preserve:

- indentation
- numbering
- spacing before bullets
- Roman numerals
- alphabetic clause numbering (a), (b), (c)

{structure_rule}

Return ONLY the translated {content_type}.

Page {page_number}
Paragraph {paragraph_number}

Text:

{paragraph}
"""
            cache_key = (language, paragraph)

            if cache_key in TRANSLATION_CACHE:
                translated = TRANSLATION_CACHE[cache_key]
            else:
                try:
                    translated = generate(prompt).strip()
                    translated = translated.strip()

                    TRANSLATION_CACHE[cache_key] = translated
                except Exception:
                    translated = paragraph

            translated = translated.strip()

            if translated:
                translated_paragraphs.append(translated)
        translations.append({
    "page": page_number,
    "language": language,
    "translation": "\n\n".join(translated_paragraphs),
    "is_blank_page": False,
})
    return translations
def translate_answer(answer: str, language: str) -> str:
    """
    Translate legal text completely into the target language (Hindi, Kannada, etc.).
    """
    if not answer or language == "English":
        return answer

    prompt = f"""
You are an expert professional legal translator specializing in Indian languages ({language}).

Your task is to translate the following legal text completely into {language}.

TRANSLATION INSTRUCTIONS:
1. Translate EVERY single sentence, paragraph, heading, bullet point, explanation, duty, and entitlement into fluent, natural {language}.
2. Translate all headings (e.g. "Document Type", "Parties Involved", "Key Obligations", "Document Summary", "Risks Detected") into {language}.
3. DO NOT leave sentences untranslated in English. Every bullet point must be fully written in {language}.
4. Keep proper names (people, places like Mangaluru), numbers, dates, and currency values intact.
5. Maintain all markdown formatting (headings, lists, bold text).

Return ONLY the complete translated text in {language}.

Text to translate:
{answer}
"""

    return generate(prompt).strip()
