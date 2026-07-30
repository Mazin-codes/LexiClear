from rag.vector_store import load_vector_db
from rag.embeddings import get_embedding_model

PERSIST_DIRECTORY = "./chroma_docs"


def get_retriever(
    vector_db,
    k=5,
    fetch_k=20,
    search_type="mmr"
):
    """
    Create a retriever from a Chroma vector database.
    """
    return vector_db.as_retriever(
        search_type=search_type,
        search_kwargs={
            "k": k,
            "fetch_k": fetch_k
        }
    )


def retrieve_context(question):
    """
    Retrieve relevant chunks from the uploaded document.
    """

    embeddings = get_embedding_model()

    vector_db = load_vector_db(
        embeddings=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    retriever = get_retriever(vector_db)

    return retriever.invoke(question)