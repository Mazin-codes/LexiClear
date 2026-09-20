from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

expected = "The employee must pay a penalty of Rs. 2 lakhs."

predicted = "The penalty for breaking the bond is Rs. 2 lakhs."

emb1 = model.encode([expected])
emb2 = model.encode([predicted])

score = cosine_similarity(emb1, emb2)[0][0]

print(f"Similarity: {score:.4f}")