from langchain_chroma import Chroma


def create_vector_db(chunks, embeddings, persist_directory):

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )


def load_vector_db(embeddings, persist_directory):

    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )