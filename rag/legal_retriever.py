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

    # Load embedding model
    embeddings = get_embedding_model()

    # Load legal vector database
    vector_db = load_vector_db(
        embeddings=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    # Get uploaded document type
    document_type = get_document_type()

    # Fallback if classification hasn't happened
    if document_type is None:
        document_type = "other"

    # Get legal domains to search
    domains = get_domains(document_type)

    print("\n========== LEGAL RETRIEVER ==========")
    print("Document Type :", document_type)
    print("Searching     :", domains)

    # Retrieve only relevant legal documents
    results = vector_db.similarity_search(
        query=question,
        k=3,
        filter={
            "domain": {
                "$in": domains
            }
        }
    )

    print(f"Retrieved {len(results)} legal documents\n")

    for i, doc in enumerate(results, start=1):
        print(f"LEGAL DOCUMENT {i}")
        print("Metadata:", doc.metadata)
        print(doc.page_content[:300])
        print("-" * 80)

    return results