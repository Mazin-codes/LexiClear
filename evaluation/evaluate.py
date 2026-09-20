import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm

from extract_answer import extract_direct_answer

API_URL = "http://127.0.0.1:8000/ask"

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "evaluation.xlsx"
OUTPUT_FILE = BASE_DIR / "results.xlsx"

df = pd.read_excel(INPUT_FILE)

results = []

print(f"Evaluating {len(df)} questions...\n")

for _, row in tqdm(df.iterrows(), total=len(df)):

    question = str(row["question"])
    expected = str(row["expected_answer"])

    try:

        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=120
        )

        if response.status_code == 200:

            answer = response.json()["answer"]
            ai_answer = extract_direct_answer(answer)

        else:

            ai_answer = f"HTTP ERROR {response.status_code}"

    except Exception as e:

        ai_answer = str(e)

    results.append({
        "Question": question,
        "Expected Answer": expected,
        "AI Answer": ai_answer
    })

results_df = pd.DataFrame(results)

results_df.to_excel(
    OUTPUT_FILE,
    index=False
)

print("\nEvaluation Completed.")
print(f"Saved to {OUTPUT_FILE}")