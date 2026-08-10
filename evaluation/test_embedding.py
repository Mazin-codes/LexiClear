from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

s1 = "Yes. The company may transfer the employee to any branch or sister concern in India or outside India."

s2 = "Yes, the company can transfer the employee to another branch."

e1 = model.encode([s1])
e2 = model.encode([s2])

print(cosine_similarity(e1, e2)[0][0])