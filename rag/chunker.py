import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


SECTION_PATTERN = re.compile(
    r"^\s*(\d+[A-Za-z]?)\.\s+([^\n—]{3,120}?)(?:\s*\.?—|\s*$)",
    re.MULTILINE,
)


def extract_section(text):
    """Return the first numbered statutory section found in a chunk."""
    match = SECTION_PATTERN.search(text)

    if match is None:
        return None

    number, heading = match.groups()
    heading = " ".join(heading.split())
    return f"Section {number} — {heading.rstrip('.') }"


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    # Add unique chunk IDs
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = idx

        section = extract_section(chunk.page_content)
        if section:
            chunk.metadata["section"] = section

    return chunks
