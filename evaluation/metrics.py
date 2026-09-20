import re
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from bert_score import score


# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "results.xlsx"
OUTPUT_FILE = BASE_DIR / "results_with_metrics.xlsx"
METRICS_FILE = BASE_DIR / "metrics.txt"


# ==========================================================
# LOAD RESULTS
# ==========================================================

print("Loading evaluation results...")

df = pd.read_excel(INPUT_FILE)

required_columns = [
    "Question",
    "Expected Answer",
    "AI Answer"
]

for column in required_columns:
    if column not in df.columns:
        raise ValueError(
            f"Missing required column: {column}"
        )

print(f"Loaded {len(df)} questions.\n")


# ==========================================================
# LOAD SENTENCE TRANSFORMER
# ==========================================================

print("Loading SentenceTransformer model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Model Loaded.\n")


# ==========================================================
# CALCULATE SEMANTIC SIMILARITY
# ==========================================================

semantic_scores = []

print("Calculating Semantic Similarity...\n")

for _, row in df.iterrows():

    expected = str(row["Expected Answer"])
    predicted = str(row["AI Answer"])

    emb_expected = model.encode(
        [expected]
    )

    emb_predicted = model.encode(
        [predicted]
    )

    similarity = cosine_similarity(
        emb_expected,
        emb_predicted
    )[0][0]

    semantic_scores.append(
        float(similarity)
    )


df["Semantic Similarity"] = [
    round(score, 4)
    for score in semantic_scores
]


# ==========================================================
# CALCULATE BERTSCORE
# ==========================================================

print("Calculating BERTScore...\n")

expected_answers = [
    str(x)
    for x in df["Expected Answer"]
]

predicted_answers = [
    str(x)
    for x in df["AI Answer"]
]

try:

    precision, recall, f1 = score(
        predicted_answers,
        expected_answers,
        lang="en",
        verbose=True
    )

    df["BERTScore Precision"] = [
        round(x.item(), 4)
        for x in precision
    ]

    df["BERTScore Recall"] = [
        round(x.item(), 4)
        for x in recall
    ]

    df["BERTScore F1"] = [
        round(x.item(), 4)
        for x in f1
    ]

except Exception as e:

    print("BERTScore calculation failed:")
    print(e)

    df["BERTScore Precision"] = 0.0
    df["BERTScore Recall"] = 0.0
    df["BERTScore F1"] = 0.0


# ==========================================================
# SIMPLE QA CORRECTNESS
# ==========================================================

def normalize_text(text):

    text = str(text).lower()

    text = re.sub(
        r"[^\w\s]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def calculate_qa_correctness(
    expected,
    predicted,
    threshold=0.70
):

    expected_norm = normalize_text(
        expected
    )

    predicted_norm = normalize_text(
        predicted
    )

    # Exact match
    if expected_norm == predicted_norm:
        return 1

    # Semantic match
    expected_embedding = model.encode(
        [expected]
    )

    predicted_embedding = model.encode(
        [predicted]
    )

    similarity = cosine_similarity(
        expected_embedding,
        predicted_embedding
    )[0][0]

    if similarity >= threshold:
        return 1

    return 0


print("Calculating QA correctness...\n")

correctness_scores = []

for _, row in df.iterrows():

    expected = str(
        row["Expected Answer"]
    )

    predicted = str(
        row["AI Answer"]
    )

    correctness = calculate_qa_correctness(
        expected,
        predicted
    )

    correctness_scores.append(
        correctness
    )


df["QA Correct"] = correctness_scores


# ==========================================================
# OVERALL METRICS
# ==========================================================

average_similarity = df[
    "Semantic Similarity"
].mean()

average_bert_precision = df[
    "BERTScore Precision"
].mean()

average_bert_recall = df[
    "BERTScore Recall"
].mean()

average_bert_f1 = df[
    "BERTScore F1"
].mean()

qa_accuracy = df[
    "QA Correct"
].mean()


# ==========================================================
# SAVE DETAILED RESULTS
# ==========================================================

df.to_excel(
    OUTPUT_FILE,
    index=False
)


# ==========================================================
# SAVE METRICS REPORT
# ==========================================================

with open(
    METRICS_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "============================================\n"
    )

    f.write(
        "LexiClear Evaluation Report\n"
    )

    f.write(
        "============================================\n\n"
    )

    f.write(
        f"Questions Evaluated : {len(df)}\n\n"
    )

    f.write(
        f"Average Semantic Similarity : "
        f"{average_similarity:.4f}\n"
    )

    f.write(
        f"Average BERTScore Precision : "
        f"{average_bert_precision:.4f}\n"
    )

    f.write(
        f"Average BERTScore Recall : "
        f"{average_bert_recall:.4f}\n"
    )

    f.write(
        f"Average BERTScore F1 : "
        f"{average_bert_f1:.4f}\n"
    )

    f.write(
        f"QA Accuracy : "
        f"{qa_accuracy:.4f}\n"
    )

    f.write("\n")

    f.write(
        "Note:\n"
    )

    f.write(
        "Semantic Similarity and BERTScore measure "
        "similarity between expected and generated answers.\n"
    )

    f.write(
        "QA Accuracy is calculated using a semantic "
        "similarity threshold of 0.70.\n"
    )


# ==========================================================
# DISPLAY RESULTS
# ==========================================================

print("\n============================================")
print("Evaluation Metrics")
print("============================================")

print(
    f"\nQuestions Evaluated : {len(df)}"
)

print(
    f"Average Semantic Similarity : "
    f"{average_similarity:.4f}"
)

print(
    f"Average BERTScore Precision : "
    f"{average_bert_precision:.4f}"
)

print(
    f"Average BERTScore Recall : "
    f"{average_bert_recall:.4f}"
)

print(
    f"Average BERTScore F1 : "
    f"{average_bert_f1:.4f}"
)

print(
    f"QA Accuracy : "
    f"{qa_accuracy:.4f}"
)

print("\n--------------------------------------------")

print(
    f"Detailed results saved to:\n"
    f"{OUTPUT_FILE}"
)

print(
    f"\nMetrics report saved to:\n"
    f"{METRICS_FILE}"
)

print("============================================")