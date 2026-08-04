from rag.retriever import retrieve_context
from rag.legal_retriever import retrieve_legal_context


def _format_documents(documents):
    """
    Format retrieved documents into readable context.
    """

    formatted = []

    for i, doc in enumerate(documents, start=1):

        source = doc.metadata.get("title") or doc.metadata.get("source") or "Uploaded Document"
        page = doc.metadata.get("page", "Unknown")
        section = doc.metadata.get("section")

        citation = f"{source}, page {page}"
        if section:
            citation = f"{source}, {section}, page {page}"

        formatted.append(
            f"""
Document {i}
Source: {source}
Page: {page}
Citation: {citation}

{doc.page_content}
"""
        )

    return "\n\n".join(formatted)


def build_context(question):
    """
    Retrieve and combine contexts from:
    1. Uploaded document
    2. Legal knowledge base
    """

    document_chunks = retrieve_context(question)
    legal_chunks = retrieve_legal_context(question)

    return {
        "document_context": _format_documents(document_chunks),
        "legal_context": _format_documents(legal_chunks),
        "document_chunks": document_chunks,
        "legal_chunks": legal_chunks
    }
