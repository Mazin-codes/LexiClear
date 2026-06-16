from langchain_chroma import Chroma

def create_vector_db(chunks, embeddings):

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    return db