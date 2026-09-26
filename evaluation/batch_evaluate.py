"""
batch_evaluate.py
=================
Batch evaluation script for LexiClear RAG system.

Evaluates multiple PDF documents, each with its own question set.
For each PDF:
  1. Clears the existing ChromaDB vector store
  2. Loads and indexes the PDF
  3. Runs the full RAG evaluation with the matching questions
  4. Saves results into a separate output folder

Usage
-----
  # Evaluate all datasets in evaluation/datasets/:
  python evaluation/batch_evaluate.py

  # Limit to first N questions per PDF (for quick testing):
  python evaluation/batch_evaluate.py --questions 5

  # Skip LLM-judge metrics:
  python evaluation/batch_evaluate.py --no-llm-judge

  # Use a custom delay between questions (seconds):
  python evaluation/batch_evaluate.py --delay 2.0

Folder Structure
----------------
  evaluation/
    datasets/
      pdf1/
        document.pdf       <- any .pdf file
        questions.xlsx      <- columns: question, expected_answer
      pdf2/
        document.pdf
        questions.xlsx
      pdf3/
        document.pdf
        questions.xlsx
    results/
      pdf1/                <- auto-created by this script
      pdf2/
      pdf3/
      batch_summary.md     <- combined summary across all PDFs
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=str(_PROJECT_ROOT / ".env"))

import pandas as pd

# Existing RAG modules (read-only)
from rag.loader import load_pdf
from rag.vectordb import create_document_vector_db, PERSIST_DIRECTORY
from rag.document_classifier import classify_document

# Evaluation modules
from evaluation.evaluate_rag import run_evaluation, parse_args as eval_parse_args


# ===========================================================================
# PATHS
# ===========================================================================
DATASETS_DIR = _SCRIPT_DIR / "datasets"
RESULTS_DIR = _SCRIPT_DIR / "results"
GRAPHS_DIR = _SCRIPT_DIR / "graphs"


# ===========================================================================
# ARGUMENT PARSING
# ===========================================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LexiClear batch evaluation — test multiple PDFs"
    )
    parser.add_argument(
        "--datasets-dir",
        type=str,
        default=str(DATASETS_DIR),
        help=f"Directory containing pdf1/, pdf2/, etc. subfolders (default: {DATASETS_DIR})",
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=None,
        metavar="N",
        help="Evaluate only the first N questions per PDF (default: all).",
    )
    parser.add_argument(
        "--no-llm-judge",
        action="store_true",
        help="Skip LLM-as-judge metrics (Faithfulness, Context Recall).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Pacing delay in seconds between questions (default: 2.0s).",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        default=[],
        help="Folder names to skip (e.g. --skip pdf1)",
    )
    return parser.parse_args()


# ===========================================================================
# HELPERS
# ===========================================================================

def find_pdf(folder: Path) -> Path | None:
    """Find the first .pdf file in a folder."""
    pdfs = list(folder.glob("*.pdf"))
    return pdfs[0] if pdfs else None


def find_questions(folder: Path) -> Path | None:
    """Find the first .xlsx or .csv file in a folder (not a PDF)."""
    for ext in ["*.xlsx", "*.csv"]:
        files = [f for f in folder.glob(ext) if "result" not in f.stem.lower()]
        if files:
            return files[0]
    return None


# Removed clear_chroma_db to avoid Windows lock issues


def index_pdf(pdf_path: Path) -> str:
    """Load a PDF, classify it, and index into ChromaDB. Returns document type."""
    print(f"\n[batch] Loading PDF: {pdf_path}")
    documents = load_pdf(str(pdf_path))
    print(f"[batch] Loaded {len(documents)} pages")

    doc_type = classify_document(documents)
    print(f"[batch] Classified as: {doc_type}")

    create_document_vector_db(documents, doc_type)
    print(f"[batch] Indexed into ChromaDB successfully")

    return doc_type


def discover_datasets(datasets_dir: Path, skip_folders: list[str]) -> list[dict]:
    """Discover all valid dataset folders (each must have a PDF + questions file)."""
    datasets = []

    if not datasets_dir.exists():
        print(f"[batch] ERROR: Datasets directory not found: {datasets_dir}")
        return datasets

    for sub in sorted(datasets_dir.iterdir()):
        if not sub.is_dir():
            continue
            
        if sub.name in skip_folders:
            print(f"[batch] Skipping dataset: {sub.name}/ (requested via --skip)")
            continue

        pdf = find_pdf(sub)
        questions = find_questions(sub)

        if not pdf:
            print(f"[batch] WARNING: No PDF found in {sub.name}/, skipping")
            continue
        if not questions:
            print(f"[batch] WARNING: No questions file found in {sub.name}/, skipping")
            continue

        datasets.append({
            "name": sub.name,
            "folder": sub,
            "pdf": pdf,
            "questions": questions,
        })
        print(f"[batch] Found dataset: {sub.name}/")
        print(f"         PDF:       {pdf.name}")
        print(f"         Questions: {questions.name}")

    return datasets


# ===========================================================================
# BATCH SUMMARY
# ===========================================================================

def generate_batch_summary(
    all_results: list[dict],
    output_path: Path,
) -> None:
    """Generate a combined markdown summary across all evaluated PDFs."""
    lines = []
    lines.append("# LexiClear Batch Evaluation Summary\n")
    lines.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Total PDFs evaluated**: {len(all_results)}\n")
    lines.append("---\n")

    # Comparison table
    lines.append("## Aggregate Metrics Comparison\n")
    metrics = [
        ("context_relevance", "Context Relevance"),
        ("context_precision", "Context Precision"),
        ("context_recall", "Context Recall"),
        ("faithfulness", "Faithfulness"),
        ("answer_relevance", "Answer Relevance"),
        ("semantic_similarity", "Semantic Similarity"),
        ("bertscore_f1", "BERTScore F1"),
        ("qa_accuracy", "QA Accuracy"),
    ]

    # Table header
    header = "| Metric |"
    separator = "|--------|"
    for r in all_results:
        header += f" {r['name']} |"
        separator += "--------|"
    lines.append(header)
    lines.append(separator)

    # Table rows
    for key, label in metrics:
        row = f"| {label} |"
        for r in all_results:
            val = r.get("agg", {}).get(key)
            row += f" {f'{val:.4f}' if val is not None else 'N/A'} |"
        lines.append(row)

    lines.append("")

    # Per-PDF details
    for r in all_results:
        lines.append(f"\n## {r['name']}")
        lines.append(f"- **PDF**: `{r['pdf_name']}`")
        lines.append(f"- **Document Type**: `{r.get('doc_type', 'unknown')}`")
        lines.append(f"- **Questions Evaluated**: {r.get('questions_evaluated', '?')}")
        lines.append(f"- **Status**: {'✅ Success' if r.get('success') else '❌ Failed'}")
        if r.get("error"):
            lines.append(f"- **Error**: {r['error']}")
        lines.append(f"- **Results Dir**: `{r.get('results_dir', '')}`")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[batch] Summary saved: {output_path}")


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> None:
    args = parse_args()
    datasets_dir = Path(args.datasets_dir)

    print("\n" + "=" * 70)
    print("  LexiClear BATCH Evaluation")
    print("=" * 70)

    # Discover all datasets
    datasets = discover_datasets(datasets_dir, args.skip)

    if not datasets:
        print("\n[batch] No valid datasets found! Please add PDFs and question files to:")
        print(f"  {datasets_dir}/pdf1/")
        print(f"  {datasets_dir}/pdf2/")
        print(f"  {datasets_dir}/pdf3/")
        print("\nEach folder needs:")
        print("  - One .pdf file (the document)")
        print("  - One .xlsx or .csv file (columns: question, expected_answer)")
        sys.exit(1)

    all_results = []

    for i, ds in enumerate(datasets, 1):
        print("\n" + "=" * 70)
        print(f"  BATCH [{i}/{len(datasets)}] — {ds['name']}")
        print(f"  PDF: {ds['pdf'].name}")
        print(f"  Questions: {ds['questions'].name}")
        print("=" * 70)

        result = {
            "name": ds["name"],
            "pdf_name": ds["pdf"].name,
            "success": False,
            "error": None,
            "agg": {},
        }

        try:
            # Step 1: Set up output directories for this dataset
            ds_results_dir = RESULTS_DIR / ds["name"]
            ds_graphs_dir = GRAPHS_DIR / ds["name"]
            ds_chroma_dir = ds_results_dir / "chroma_docs"
            
            ds_results_dir.mkdir(parents=True, exist_ok=True)
            ds_graphs_dir.mkdir(parents=True, exist_ok=True)
            ds_chroma_dir.mkdir(parents=True, exist_ok=True)
            
            result["results_dir"] = str(ds_results_dir)

            # Override ChromaDB directories to avoid Windows file locks
            import rag.vectordb as vdb_mod
            import rag.retriever as ret_mod
            orig_vdb_dir = vdb_mod.PERSIST_DIRECTORY
            orig_ret_dir = ret_mod.PERSIST_DIRECTORY
            
            vdb_mod.PERSIST_DIRECTORY = str(ds_chroma_dir)
            ret_mod.PERSIST_DIRECTORY = str(ds_chroma_dir)

            # Step 2: Index the PDF into the new unique ChromaDB
            doc_type = index_pdf(ds["pdf"])
            result["doc_type"] = doc_type

            # Step 3: Build eval args (simulate command-line args for evaluate_rag)
            eval_argv = [
                "--input-file", str(ds["questions"]),
                "--delay", str(args.delay),
            ]
            if args.questions is not None:
                eval_argv += ["--questions", str(args.questions)]
            if args.no_llm_judge:
                eval_argv.append("--no-llm-judge")

            # Temporarily override output paths in evaluate_rag module
            import evaluation.evaluate_rag as eval_mod
            orig_results_dir = eval_mod.RESULTS_DIR
            orig_graphs_dir = eval_mod.GRAPHS_DIR
            orig_csv = eval_mod.CSV_OUTPUT
            orig_xlsx = eval_mod.XLSX_OUTPUT
            orig_agg = eval_mod.AGG_OUTPUT
            orig_report = eval_mod.REPORT_OUTPUT
            orig_checkpoint = eval_mod.CHECKPOINT_CSV

            eval_mod.RESULTS_DIR = ds_results_dir
            eval_mod.GRAPHS_DIR = ds_graphs_dir
            eval_mod.CSV_OUTPUT = ds_results_dir / "rag_evaluation_results.csv"
            eval_mod.XLSX_OUTPUT = ds_results_dir / "rag_evaluation_results.xlsx"
            eval_mod.AGG_OUTPUT = ds_results_dir / "aggregate_metrics.csv"
            eval_mod.REPORT_OUTPUT = ds_results_dir / "evaluation_report.md"
            eval_mod.CHECKPOINT_CSV = ds_results_dir / "checkpoint_results.csv"

            # Step 4: Parse args and run
            old_argv = sys.argv
            sys.argv = ["evaluate_rag.py"] + eval_argv
            eval_args = eval_parse_args()
            sys.argv = old_argv

            run_evaluation(eval_args)

            # Step 5: Read back aggregate metrics
            agg_path = ds_results_dir / "aggregate_metrics.csv"
            if agg_path.exists():
                agg_df = pd.read_csv(agg_path)
                result["agg"] = agg_df.iloc[0].to_dict()
                result["questions_evaluated"] = int(agg_df.iloc[0].get("questions_evaluated", 0))

            result["success"] = True
            print(f"\n[batch] ✅ {ds['name']} completed successfully!")

        except Exception as exc:
            result["error"] = str(exc)
            print(f"\n[batch] ❌ {ds['name']} FAILED: {exc}")
            traceback.print_exc()

        finally:
            # Restore original paths
            eval_mod.RESULTS_DIR = orig_results_dir
            eval_mod.GRAPHS_DIR = orig_graphs_dir
            eval_mod.CSV_OUTPUT = orig_csv
            eval_mod.XLSX_OUTPUT = orig_xlsx
            eval_mod.AGG_OUTPUT = orig_agg
            eval_mod.REPORT_OUTPUT = orig_report
            eval_mod.CHECKPOINT_CSV = orig_checkpoint
            vdb_mod.PERSIST_DIRECTORY = orig_vdb_dir
            ret_mod.PERSIST_DIRECTORY = orig_ret_dir

        all_results.append(result)

    # -----------------------------------------------------------------------
    # Generate batch summary
    # -----------------------------------------------------------------------
    summary_path = RESULTS_DIR / "batch_summary.md"
    generate_batch_summary(all_results, summary_path)

    # Final output
    print("\n" + "=" * 70)
    print("  BATCH EVALUATION COMPLETE")
    print("=" * 70)
    successes = sum(1 for r in all_results if r["success"])
    print(f"  Passed: {successes} / {len(all_results)}")
    for r in all_results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['name']} ({r['pdf_name']})")
    print(f"\n  Summary: {summary_path}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[batch] Interrupted by user.")
        sys.exit(1)
