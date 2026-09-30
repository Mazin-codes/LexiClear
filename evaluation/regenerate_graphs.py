from pathlib import Path
import pandas as pd

from rag_graphs import generate_all_graphs


# ------------------------------------------------------------
# Existing evaluation results
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = BASE_DIR / "results"
GRAPHS_DIR = BASE_DIR / "graphs"

RESULTS_CSV = RESULTS_DIR / "rag_evaluation_results.csv"
AGGREGATE_CSV = RESULTS_DIR / "aggregate_metrics.csv"


# ------------------------------------------------------------
# Load existing results
# ------------------------------------------------------------

print("=" * 70)
print("  REGENERATING GRAPHS FROM EXISTING EVALUATION RESULTS")
print("=" * 70)

print(f"\nResults CSV   : {RESULTS_CSV}")
print(f"Aggregate CSV : {AGGREGATE_CSV}")
print(f"Graphs output : {GRAPHS_DIR}")


if not RESULTS_CSV.exists():
    raise FileNotFoundError(
        f"Results CSV not found:\n{RESULTS_CSV}"
    )

if not AGGREGATE_CSV.exists():
    raise FileNotFoundError(
        f"Aggregate CSV not found:\n{AGGREGATE_CSV}"
    )


# ------------------------------------------------------------
# Read existing 80-question results
# ------------------------------------------------------------

df = pd.read_csv(RESULTS_CSV)

# Aggregate CSV contains one row with all aggregate metrics.
agg_df = pd.read_csv(AGGREGATE_CSV)

if agg_df.empty:
    raise ValueError("Aggregate metrics CSV is empty.")

agg = agg_df.iloc[0].to_dict()


# ------------------------------------------------------------
# Generate graphs ONLY
# ------------------------------------------------------------

GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

generated = generate_all_graphs(
    df=df,
    agg=agg,
    output_dir=GRAPHS_DIR,
)


# ------------------------------------------------------------
# Final output
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("  GRAPH GENERATION COMPLETE")
print("=" * 70)

print(f"\nQuestions in existing results : {len(df)}")
print(f"Graphs generated              : {len(generated)}")

for graph in generated:
    print(f"  - {graph.name}")

print("\nNo questions were re-evaluated.")
print("No LLM calls were made by this script.")
print("Existing evaluation results were not modified.")
print("=" * 70)