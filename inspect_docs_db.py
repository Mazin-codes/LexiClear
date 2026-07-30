from rag.embeddings import get_embedding_model
from rag.vector_store import load_vector_db

embeddings = get_embedding_model()

import os

print("Loading from:", os.path.abspath("./chroma_docs"))

db = load_vector_db(
    embeddings=embeddings,
    persist_directory="./chroma_docs"
)

print("Documents indexed:", db._collection.count())