def explain_retrieval(docs):
    """
    Returns metadata about retrieved chunks.
    """

    explanation = []

    for doc in docs:

        page = doc.metadata.get("page", 0) + 1
        chunk = doc.metadata.get("chunk_id", "N/A")

        preview = doc.page_content[:180].replace("\n", " ")

        explanation.append({
            "page": page,
            "chunk": chunk,
            "preview": preview
        })

    return explanation