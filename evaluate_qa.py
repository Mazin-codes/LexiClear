import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from rag.loader import load_pdf
from rag.chunker import split_documents
from rag.embeddings import get_embedding_model
from rag.vectordb import create_vector_db
from rag.retriever import get_retriever
from rag.llm import generate_answer, generate_short_answer

# Load PDF
documents = load_pdf("sample.pdf")
chunks = split_documents(documents)

embeddings = get_embedding_model()
db = create_vector_db(chunks, embeddings)
retriever = get_retriever(db)

# Similarity model
model = SentenceTransformer("all-MiniLM-L6-v2")

test_data = pd.read_csv("qa_test.csv")

correct = 0

for _, row in test_data.iterrows():

    question = row["question"]
    expected = row["expected_answer"]

    results = retriever.invoke(question)
    predicted = generate_short_answer(question, results)

    emb1 = model.encode(expected)
    emb2 = model.encode(predicted)

    score = cosine_similarity(
        [emb1],
        [emb2]
    )[0][0]

    print("\n" + "="*60)
    print("Question :", question)
    print("Expected :", expected)
    print("Predicted:", predicted[:500])
    print("Score    :", round(score, 2))

    if score >= 0.80:
        correct += 1

accuracy = (
    correct / len(test_data)
) * 100

print("\n" + "="*60)
print(f"QA Accuracy: {accuracy:.2f}%")
print("="*60)