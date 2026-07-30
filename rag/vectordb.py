from rag.chunker import split_documents
from rag.embeddings import get_embedding_model
from rag.vector_store import create_vector_db

PERSIST_DIRECTORY = "./chroma_docs"


def create_document_vector_db(documents, document_type):

    chunks = split_documents(documents)

    for chunk in chunks:
        chunk.metadata["document_type"] = document_type

    # DEBUG
    print("\nFIRST CHUNK METADATA BEFORE SAVING")
    print(chunks[0].metadata)

    embeddings = get_embedding_model()

    db = create_vector_db(
        chunks=chunks,
        embeddings=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    # DEBUG
    print("\nFIRST CHUNK METADATA AFTER SAVING")
    test = db.similarity_search("lease", k=1)
    print(test[0].metadata)

    return db