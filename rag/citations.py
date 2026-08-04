"""Formatting utilities for legal-reference citations."""


def format_legal_citations(documents):
    """Create a stable, de-duplicated citation list from retrieved legal chunks."""
    citations = []
    seen = set()

    for document in documents:
        metadata = document.metadata
        title = metadata.get("title") or metadata.get("file_name") or "Legal reference"
        section = metadata.get("section")
        page = metadata.get("page_label")

        if page is None and isinstance(metadata.get("page"), int):
            page = str(metadata["page"] + 1)

        parts = [title]
        if section:
            parts.append(section)
        if page is not None:
            parts.append(f"p. {page}")

        citation = " — ".join(parts)
        if citation not in seen:
            seen.add(citation)
            citations.append(citation)

    return citations


def format_legal_sources(documents):
    """Return a Markdown source section for retrieved legal chunks."""
    citations = format_legal_citations(documents)

    if not citations:
        return ""

    return "\n\n---\n\n## Legal Sources\n\n" + "\n".join(
        f"- {citation}" for citation in citations
    )
