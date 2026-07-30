from rag.embeddings import get_embedding_model
from rag.vector_store import load_vector_db

embeddings = get_embedding_model()

db = load_vector_db(
    embeddings=embeddings,
    persist_directory="./chroma_docs"
)

docs = db.similarity_search("rent", k=1)

print(docs[0].metadata)