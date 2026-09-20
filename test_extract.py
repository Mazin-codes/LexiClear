import requests
from evaluation.extract_answer import extract_direct_answer

url = "http://127.0.0.1:8000/ask"

response = requests.post(
    url,
    json={"question":"What is the probationary period?"}
)

answer = response.json()["answer"]

print("FULL RESPONSE\n")
print(answer)

print("\n\nDIRECT ANSWER\n")

print(extract_direct_answer(answer))