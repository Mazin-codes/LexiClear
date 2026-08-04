from rag.vector_store import load_vector_db
from rag.embeddings import get_embedding_model
from rag.session import get_document_type
from rag.legal_router import get_domains

PERSIST_DIRECTORY = "./chroma_legal"


def retrieve_legal_context(question):
    """
    Retrieve relevant legal references based on the
    uploaded document type.
    """

    embeddings = get_embedding_model()

    vector_db = load_vector_db(
        embeddings=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    document_type = get_document_type()

    if document_type is None:
        document_type = "other"

    domains = get_domains(document_type)

    print("\n========== LEGAL RETRIEVER ==========")
    print("Document Type :", document_type)
    print("Searching Domains :", domains)

    results = []

    # Search each legal domain separately
    for domain in domains:

        print(f"\nSearching domain: {domain}")

        docs = vector_db.similarity_search(
            query=question,
            k=3,
            filter={
                "domain": domain
            }
        )

        print(f"Retrieved {len(docs)} documents")

        results.extend(docs)

    # Remove duplicates
    unique_results = []
    seen = set()

    for doc in results:

        key = (
            doc.metadata.get("source"),
            doc.metadata.get("page"),
            doc.page_content[:100]
        )

        if key not in seen:
            seen.add(key)
            unique_results.append(doc)

    print(f"\nTotal legal documents retrieved: {len(unique_results)}\n")

    for i, doc in enumerate(unique_results, start=1):
        print(f"LEGAL DOCUMENT {i}")
        print("Metadata:", doc.metadata)
        print(doc.page_content[:300])
        print("-" * 80)

    return unique_results