# test_contract_law.py

from rag.vector_store import load_vector_db
from rag.embeddings import get_embedding_model

db = load_vector_db(
    get_embedding_model(),
    "./chroma_legal"
)

results = db.similarity_search(
    "contract",
    k=10,
    filter={"domain": "contract_law"},
)

for i, doc in enumerate(results, 1):
    print("=" * 80)
    print(i)
    print(doc.metadata)
