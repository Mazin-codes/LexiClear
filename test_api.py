import requests

url = "http://127.0.0.1:8000/ask"

payload = {
    "question": "What is the due date?"
}

response = requests.post(url, json=payload)

print(response.status_code)
print(response.json())