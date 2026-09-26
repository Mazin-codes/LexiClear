"""
evaluate_rag.py
===============
Main entry point for the LexiClear comprehensive RAG evaluation.

Usage
-----
  # Live mode (re-runs retrieval + generation for all 25 questions):
  python evaluation/evaluate_rag.py

  # Cached mode (uses existing results_with_metrics.xlsx for answer-quality
  # metrics; still runs retrieval live for context metrics):
  python evaluation/evaluate_rag.py --use-cached

  # Limit to first N questions (for quick testing):
  python evaluation/evaluate_rag.py --questions 5

  # Skip LLM-judge metrics (Faithfulness, Context Recall) — use embedding
  # fallback instead.  Faster but less accurate:
  python evaluation/evaluate_rag.py --no-llm-judge

THIS SCRIPT IS NEW AND ADDITIVE.
It does not modify any existing file.
It calls rag.* modules only in read-only observer capacity.

Pipeline
--------
1. Load evaluation.xlsx  (25 questions + expected answers)
2. For each question:
   a. Call retrieve_context() + retrieve_legal_context()  [existing, unchanged]
   b. Call build_context() + generate_answer()            [existing, unchanged]
   c. Extract Direct Answer via extract_direct_answer()   [existing, unchanged]
3. Compute all 10 metrics via rag_metrics.py              [new]
4. Save rag_evaluation_results.csv + .xlsx                [new]
5. Save aggregate_metrics.csv                             [new]
6. Generate 7 graphs via rag_graphs.py                    [new]
7. Generate evaluation_report.md via rag_report.py        [new]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Add project root to sys.path so rag.* imports work
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Now we can safely import the existing modules (READ-ONLY — unchanged)
from dotenv import load_dotenv
load_dotenv(dotenv_path=str(_PROJECT_ROOT / ".env"))

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Existing modules — imported read-only, never modified
from rag.retriever import retrieve_context
from rag.legal_retriever import retrieve_legal_context
from rag.context_fusion import build_context
from rag.llm import generate_answer

# Evaluation modules — all new
from evaluation.rag_metrics import (
    compute_semantic_similarity,
    compute_bertscore,
    compute_qa_correctness,
    compute_context_relevance,
    compute_faithfulness,
    compute_answer_relevance,
    compute_context_precision,
    compute_context_recall,
    extract_chunk_metadata,
    build_retrieved_context_text,
)
from evaluation.rag_graphs import generate_all_graphs
from evaluation.rag_report import generate_report

# extract_direct_answer from existing module — read-only
sys.path.insert(0, str(_SCRIPT_DIR))
from extract_answer import extract_direct_answer


# ===========================================================================
# OUTPUT PATHS
# ===========================================================================
RESULTS_DIR = _SCRIPT_DIR / "results"
GRAPHS_DIR  = _SCRIPT_DIR / "graphs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

CSV_OUTPUT   = RESULTS_DIR / "rag_evaluation_results.csv"
XLSX_OUTPUT  = RESULTS_DIR / "rag_evaluation_results.xlsx"
AGG_OUTPUT   = RESULTS_DIR / "aggregate_metrics.csv"
REPORT_OUTPUT = RESULTS_DIR / "evaluation_report.md"
CHECKPOINT_CSV = RESULTS_DIR / "checkpoint_results.csv"

# Input
EVAL_XLSX    = _SCRIPT_DIR / "evaluation.xlsx"
CACHED_XLSX  = _SCRIPT_DIR / "results_with_metrics.xlsx"


# ===========================================================================
# ARGUMENT PARSING
# ===========================================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LexiClear comprehensive RAG evaluation"
    )
    parser.add_argument(
        "--input-file",
        nargs="+",
        default=None,
        metavar="FILE",
        help="Path to one or more Excel (.xlsx) or CSV (.csv) files containing questions. "
             "If multiple files are given, they are merged into a single evaluation run.",
    )
    parser.add_argument(
        "--use-cached",
        action="store_true",
        help="Use existing results_with_metrics.xlsx for AI answers instead of "
             "re-generating them. Retrieval still runs live.",
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=None,
        metavar="N",
        help="Evaluate only the first N questions (default: all).",
    )
    parser.add_argument(
        "--no-llm-judge",
        action="store_true",
        help="Skip LLM-as-judge metrics (Faithfulness, Context Recall). "
             "Use embedding-based fallback instead.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing checkpoint file if a previous run was interrupted.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Pacing delay in seconds between questions to prevent rate-limit bursts (default: 1.5s).",
    )
    return parser.parse_args()


# ===========================================================================
# LOAD DATASET
# ===========================================================================
def load_dataset(input_files: list[str] | None, n: int | None) -> tuple[pd.DataFrame, int]:
    if not input_files:
        target_files = [EVAL_XLSX]
    else:
        target_files = [Path(f) for f in input_files]

    dfs: list[pd.DataFrame] = []
    for raw_path in target_files:
        resolved = raw_path
        if not resolved.exists():
            resolved = _SCRIPT_DIR / raw_path
        if not resolved.exists():
            raise FileNotFoundError(f"[evaluate_rag] Input file not found: {raw_path}")

        print(f"\n[evaluate_rag] Loading dataset: {resolved}")
        if resolved.suffix.lower() == ".csv":
            sub_df = pd.read_csv(resolved)
        else:
            sub_df = pd.read_excel(resolved)

        # Resilient column name matching
        q_col = None
        ans_col = None
        for col in sub_df.columns:
            clean = str(col).strip().lower().replace(" ", "_")
            if clean in ["question", "questions", "q", "query"]:
                q_col = col
            elif clean in ["expected_answer", "expected", "answer", "answers", "target"]:
                ans_col = col

        if not q_col:
            raise KeyError(
                f"[evaluate_rag] Could not find question column in {resolved}. "
                f"Available columns: {sub_df.columns.tolist()}"
            )
        if not ans_col:
            sub_df["expected_answer"] = ""
            ans_col = "expected_answer"

        clean_sub = pd.DataFrame({
            "question": sub_df[q_col].astype(str).str.strip(),
            "expected_answer": sub_df[ans_col].astype(str).str.strip(),
        })
        dfs.append(clean_sub)

    combined = pd.concat(dfs, ignore_index=True)
    total = len(combined)
    print(f"[evaluate_rag] Total questions loaded across {len(target_files)} file(s): {total}")

    if n is not None:
        combined = combined.head(n)
        print(f"[evaluate_rag] Evaluating first {len(combined)} questions (--questions {n})")
    else:
        print(f"[evaluate_rag] Evaluating all {len(combined)} questions")

    return combined.reset_index(drop=True), total


def load_cached_answers(df: pd.DataFrame) -> dict[str, str]:
    """Load cached AI answers from results_with_metrics.xlsx keyed by question."""
    if not CACHED_XLSX.exists():
        print(f"[evaluate_rag] WARNING: Cached file not found: {CACHED_XLSX}")
        return {}
    cached = pd.read_excel(CACHED_XLSX)
    mapping = {}
    for _, row in cached.iterrows():
        q = str(row.get("Question", "")).strip()
        a = str(row.get("AI Answer", "")).strip()
        if q:
            mapping[q] = a
    print(f"[evaluate_rag] Loaded {len(mapping)} cached answers.")
    return mapping


# ===========================================================================
# RETRIEVAL HELPER
# ===========================================================================
def run_retrieval(question: str) -> dict:
    """
    Run the existing LexiClear retrieval pipeline.
    Returns a dict with all raw outputs.
    Does NOT modify any existing module.
    """
    # Call the existing retrieve_context and retrieve_legal_context directly
    doc_chunks   = retrieve_context(question)
    legal_chunks = retrieve_legal_context(question)

    from rag.context_fusion import _format_documents
    context = {
        "document_context": _format_documents(doc_chunks),
        "legal_context":    _format_documents(legal_chunks),
        "document_chunks":  doc_chunks,
        "legal_chunks":     legal_chunks,
    }

    return {
        "context":       context,
        "doc_chunks":    doc_chunks,
        "legal_chunks":  legal_chunks,
        "all_chunks":    doc_chunks + legal_chunks,
    }


# ===========================================================================
# DOCUMENT CONTEXT WARNING
# ===========================================================================
def detect_document_mismatch(answers: list[str]) -> str:
    """
    Heuristic: if many answers contain "does not contain" or "does not state",
    warn that the loaded document may not match the QA dataset.
    """
    keywords = ["does not contain", "does not state", "not specified",
                "does not address", "no information"]
    count = sum(
        1 for a in answers
        if any(k.lower() in a.lower() for k in keywords)
    )
    if count > len(answers) * 0.5:
        return (
            f"{count}/{len(answers)} AI answers indicate the model could not find "
            "relevant information in the loaded document. This strongly suggests "
            "that `chroma_docs/` currently contains a different document than the "
            "one the QA dataset was designed for (employment contract). "
            "The evaluation metrics reflect retrieval against the CURRENTLY LOADED "
            "document, not necessarily against the employment contract."
        )
    return ""


# ===========================================================================
# MAIN EVALUATION LOOP
# ===========================================================================
def run_evaluation(args: argparse.Namespace) -> None:

    print("\n" + "="*70)
    print("  LexiClear Comprehensive RAG Evaluation")
    print("="*70)

    # Load dataset
    df, total_questions = load_dataset(args.input_file, args.questions)
    questions_evaluated = len(df)

    # Optionally load cached answers
    cached_answers = {}
    if args.use_cached:
        cached_answers = load_cached_answers(df)

    # Load sentence transformer (same model as existing evaluation)
    print("\n[evaluate_rag] Loading SentenceTransformer (all-MiniLM-L6-v2)...")
    st_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("[evaluate_rag] Model loaded.")

    # Per-question records & Checkpoint resumption
    records: list[dict] = []
    ai_answers_collected: list[str] = []
    completed_questions: set[str] = set()

    if args.resume and CHECKPOINT_CSV.exists():
        try:
            chk_df = pd.read_csv(CHECKPOINT_CSV)
            records = chk_df.to_dict(orient="records")
            ai_answers_collected = [str(r.get("ai_answer", "")) for r in records]
            completed_questions = {str(r.get("question", "")).strip() for r in records}
            print(f"[evaluate_rag] Resuming from checkpoint: {len(records)} questions already evaluated.")
        except Exception as exc:
            print(f"[evaluate_rag] Could not read checkpoint ({exc}), starting fresh.")
            records = []
            ai_answers_collected = []
            completed_questions = set()

    print(f"\n[evaluate_rag] Starting evaluation of {questions_evaluated} questions...\n")

    for idx, row in tqdm(df.iterrows(), total=questions_evaluated, desc="Evaluating"):

        question = str(row["question"]).strip()
        expected = str(row["expected_answer"]).strip()

        if question in completed_questions:
            continue

        record: dict = {
            "question_id":   len(records) + 1,
            "question":      question,
            "expected_answer": expected,
        }

        # -------------------------------------------------------------------
        # Step 1: Retrieval (always live)
        # -------------------------------------------------------------------
        try:
            retrieval = run_retrieval(question)
            doc_chunks   = retrieval["doc_chunks"]
            legal_chunks = retrieval["legal_chunks"]
            all_chunks   = retrieval["all_chunks"]
            context      = retrieval["context"]

            # Record chunk metadata
            chunk_meta_list = []
            for rank, doc in enumerate(doc_chunks, start=1):
                m = extract_chunk_metadata(doc, rank)
                m["chunk_source"] = "document"
                chunk_meta_list.append(m)
            for rank, doc in enumerate(legal_chunks, start=1):
                m = extract_chunk_metadata(doc, rank)
                m["chunk_source"] = "legal"
                chunk_meta_list.append(m)

            record["retrieved_contexts"]        = json.dumps(
                [m["chunk_text"][:300] for m in chunk_meta_list]
            )
            record["num_doc_chunks"]            = len(doc_chunks)
            record["num_legal_chunks"]          = len(legal_chunks)
            record["num_total_chunks"]          = len(all_chunks)

            # Build combined context text for LLM judges
            doc_context_text   = build_retrieved_context_text(doc_chunks)
            legal_context_text = build_retrieved_context_text(legal_chunks)
            all_context_text   = build_retrieved_context_text(all_chunks)

            retrieval_ok = True

        except Exception as exc:
            print(f"\n[evaluate_rag] Retrieval failed for Q{idx+1}: {exc}")
            doc_chunks = legal_chunks = all_chunks = []
            context = {"document_context": "", "legal_context": "",
                       "document_chunks": [], "legal_chunks": []}
            doc_context_text = legal_context_text = all_context_text = ""
            record["retrieved_contexts"] = "[]"
            record["num_doc_chunks"] = 0
            record["num_legal_chunks"] = 0
            record["num_total_chunks"] = 0
            retrieval_ok = False

        # -------------------------------------------------------------------
        # Step 2: Answer generation (live OR cached)
        # -------------------------------------------------------------------
        if args.use_cached and question in cached_answers:
            # Use cached short answer directly
            ai_answer_short = cached_answers[question]
            ai_answer_full  = ai_answer_short
        else:
            try:
                ai_answer_full  = generate_answer(question, context)
                ai_answer_short = extract_direct_answer(ai_answer_full)
            except Exception as exc:
                print(f"\n[evaluate_rag] Answer generation failed for Q{idx+1}: {exc}")
                ai_answer_full  = f"ERROR: {exc}"
                ai_answer_short = ai_answer_full

        record["ai_answer"] = ai_answer_short
        ai_answers_collected.append(ai_answer_short)

        # -------------------------------------------------------------------
        # Step 3: Existing metrics (reproduced faithfully)
        # -------------------------------------------------------------------
        try:
            record["semantic_similarity"] = round(
                compute_semantic_similarity(expected, ai_answer_short, st_model), 4
            )
        except Exception as exc:
            print(f"[evaluate_rag] Semantic similarity failed Q{idx+1}: {exc}")
            record["semantic_similarity"] = None

        try:
            record["qa_correct"] = compute_qa_correctness(
                expected, ai_answer_short, st_model, threshold=0.70
            )
        except Exception as exc:
            print(f"[evaluate_rag] QA correctness failed Q{idx+1}: {exc}")
            record["qa_correct"] = None

        # -------------------------------------------------------------------
        # Step 4: New RAG metrics
        # -------------------------------------------------------------------

        # Context Relevance
        try:
            record["context_relevance"] = round(
                compute_context_relevance(question, all_chunks, st_model), 4
            ) if all_chunks else None
        except Exception as exc:
            print(f"[evaluate_rag] Context relevance failed Q{idx+1}: {exc}")
            record["context_relevance"] = None

        # Context Precision
        try:
            record["context_precision"] = round(
                compute_context_precision(question, all_chunks, st_model), 4
            ) if all_chunks else None
        except Exception as exc:
            print(f"[evaluate_rag] Context precision failed Q{idx+1}: {exc}")
            record["context_precision"] = None

        # Answer Relevance
        try:
            record["answer_relevance"] = round(
                compute_answer_relevance(question, ai_answer_short, st_model), 4
            )
        except Exception as exc:
            print(f"[evaluate_rag] Answer relevance failed Q{idx+1}: {exc}")
            record["answer_relevance"] = None

        # Faithfulness (LLM-judge or embedding fallback)
        try:
            use_llm = not args.no_llm_judge
            record["faithfulness"] = round(
                compute_faithfulness(ai_answer_short, all_context_text, use_llm=use_llm), 4
            ) if (ai_answer_short and all_context_text) else None
        except Exception as exc:
            print(f"[evaluate_rag] Faithfulness failed Q{idx+1}: {exc}")
            record["faithfulness"] = None

        # Context Recall (LLM-judge or embedding fallback)
        try:
            use_llm = not args.no_llm_judge
            record["context_recall"] = round(
                compute_context_recall(expected, all_context_text, use_llm=use_llm), 4
            ) if (expected and all_context_text) else None
        except Exception as exc:
            print(f"[evaluate_rag] Context recall failed Q{idx+1}: {exc}")
            record["context_recall"] = None

        records.append(record)

        # Checkpoint: save intermediate results after each question
        try:
            pd.DataFrame(records).to_csv(CHECKPOINT_CSV, index=False, encoding="utf-8")
        except Exception:
            pass

        # Pacing delay between questions to avoid Groq TPM/RPM limit bursts
        if args.delay > 0:
            time.sleep(args.delay)

    # -----------------------------------------------------------------------
    # BERTScore — batch computation for all questions
    # -----------------------------------------------------------------------
    print("\n[evaluate_rag] Computing BERTScore (batch)...")
    expected_list  = [str(r["expected_answer"]) for r in records]
    predicted_list = [str(r["ai_answer"]) for r in records]

    bert_p, bert_r, bert_f1 = compute_bertscore(expected_list, predicted_list)

    for i, record in enumerate(records):
        record["bertscore_precision"] = bert_p[i]
        record["bertscore_recall"]    = bert_r[i]
        record["bertscore_f1"]        = bert_f1[i]

    # -----------------------------------------------------------------------
    # Build results DataFrame
    # -----------------------------------------------------------------------
    results_df = pd.DataFrame(records)

    # Detect document mismatch
    doc_note = detect_document_mismatch(ai_answers_collected)
    if doc_note:
        print(f"\n[evaluate_rag] ⚠ DOCUMENT MISMATCH DETECTED:\n{doc_note}\n")

    # -----------------------------------------------------------------------
    # Aggregate metrics
    # -----------------------------------------------------------------------
    def safe_mean(col: str) -> float | None:
        if col not in results_df.columns:
            return None
        vals = results_df[col].dropna()
        return round(float(vals.mean()), 4) if len(vals) > 0 else None

    agg = {
        # New RAG metrics
        "context_relevance":  safe_mean("context_relevance"),
        "context_precision":  safe_mean("context_precision"),
        "context_recall":     safe_mean("context_recall"),
        "faithfulness":       safe_mean("faithfulness"),
        "answer_relevance":   safe_mean("answer_relevance"),
        # Existing metrics
        "semantic_similarity": safe_mean("semantic_similarity"),
        "bertscore_precision": safe_mean("bertscore_precision"),
        "bertscore_recall":    safe_mean("bertscore_recall"),
        "bertscore_f1":        safe_mean("bertscore_f1"),
        "qa_accuracy": (
            round(float(results_df["qa_correct"].mean()), 4)
            if "qa_correct" in results_df.columns
            else None
        ),
        # Metadata
        "questions_evaluated": questions_evaluated,
        "total_questions":     total_questions,
        "mode": "cached_answers+live_retrieval" if args.use_cached else "fully_live",
        "llm_judge": not args.no_llm_judge,
    }

    # -----------------------------------------------------------------------
    # Print aggregate to console
    # -----------------------------------------------------------------------
    print("\n" + "="*70)
    print("  AGGREGATE RESULTS")
    print("="*70)
    print(f"  Questions evaluated : {questions_evaluated} / {total_questions}")
    print(f"  Mode                : {agg['mode']}")
    print("")
    print("  --- New RAG Metrics ---")
    for k, label in [
        ("context_relevance",  "Context Relevance "),
        ("context_precision",  "Context Precision "),
        ("context_recall",     "Context Recall    "),
        ("faithfulness",       "Faithfulness      "),
        ("answer_relevance",   "Answer Relevance  "),
    ]:
        val = agg.get(k)
        print(f"  {label}: {f'{val:.4f}' if val is not None else 'N/A'}")
    print("")
    print("  --- Existing Metrics ---")
    for k, label in [
        ("semantic_similarity", "Semantic Similarity"),
        ("bertscore_precision", "BERTScore Precision"),
        ("bertscore_recall",    "BERTScore Recall   "),
        ("bertscore_f1",        "BERTScore F1       "),
        ("qa_accuracy",         "QA Accuracy        "),
    ]:
        val = agg.get(k)
        print(f"  {label}: {f'{val:.4f}' if val is not None else 'N/A'}")
    print("")
    if "qa_correct" in results_df.columns:
        correct = int(results_df["qa_correct"].sum())
        print(f"  QA Correct: {correct} / {questions_evaluated}")
    print("="*70)

    # Cross-check with reference
    reference = {
        "semantic_similarity": 0.5564,
        "bertscore_precision": 0.8736,
        "bertscore_recall":    0.8883,
        "bertscore_f1":        0.8807,
        "qa_accuracy":         0.1600,
    }
    print("\n  Cross-check vs. reference (from metrics.txt):")
    for k, ref in reference.items():
        val = agg.get(k)
        if val is not None:
            diff = val - ref
            flag = "✓" if abs(diff) < 0.01 else f"⚠ diff={diff:+.4f}"
            print(f"    {k}: got={val:.4f}, ref={ref:.4f}  {flag}")
    print("")

    # -----------------------------------------------------------------------
    # Save CSV
    # -----------------------------------------------------------------------
    # Column ordering for readability
    col_order = [
        "question_id", "question", "expected_answer", "ai_answer",
        "retrieved_contexts", "num_doc_chunks", "num_legal_chunks", "num_total_chunks",
        "context_relevance", "context_precision", "context_recall",
        "faithfulness", "answer_relevance",
        "semantic_similarity",
        "bertscore_precision", "bertscore_recall", "bertscore_f1",
        "qa_correct",
    ]
    ordered_cols = [c for c in col_order if c in results_df.columns]
    remaining    = [c for c in results_df.columns if c not in ordered_cols]
    results_df   = results_df[ordered_cols + remaining]

    results_df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8")
    print(f"[evaluate_rag] CSV saved : {CSV_OUTPUT}")

    results_df.to_excel(XLSX_OUTPUT, index=False)
    print(f"[evaluate_rag] XLSX saved: {XLSX_OUTPUT}")

    # Save aggregate
    agg_df = pd.DataFrame([agg])
    agg_df.to_csv(AGG_OUTPUT, index=False)
    print(f"[evaluate_rag] Aggregate saved: {AGG_OUTPUT}")

    # Clean up intermediate checkpoint file
    if CHECKPOINT_CSV.exists():
        try:
            CHECKPOINT_CSV.unlink()
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Graphs
    # -----------------------------------------------------------------------
    print("\n[evaluate_rag] Generating graphs...")
    graphs_generated = generate_all_graphs(results_df, agg, GRAPHS_DIR)
    print(f"[evaluate_rag] {len(graphs_generated)} graph(s) generated.")

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------
    print("\n[evaluate_rag] Generating evaluation report...")
    config = {
        "dataset_file":          str(EVAL_XLSX),
        "total_questions":        total_questions,
        "questions_evaluated":    questions_evaluated,
        "llm_model":              "openai/gpt-oss-120b",
        "llm_provider":           "Groq",
        "embedding_model":        "sentence-transformers/all-MiniLM-L6-v2",
        "mode":                   agg["mode"],
        "document_context_note":  doc_note,
    }
    generate_report(results_df, agg, REPORT_OUTPUT, config, graphs_generated)

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    print("\n" + "="*70)
    print("  EVALUATION COMPLETE")
    print("="*70)
    print(f"  Results CSV   : {CSV_OUTPUT}")
    print(f"  Results XLSX  : {XLSX_OUTPUT}")
    print(f"  Aggregate CSV : {AGG_OUTPUT}")
    print(f"  Report        : {REPORT_OUTPUT}")
    print(f"  Graphs dir    : {GRAPHS_DIR}")
    for g in graphs_generated:
        print(f"    - {g.name}")
    print("="*70)
    print("")
    if doc_note:
        print("⚠ IMPORTANT — Document mismatch warning was detected.")
        print("  See 'Document Context Note' section of the evaluation report.")
        print("")


# ===========================================================================
# ENTRY POINT
# ===========================================================================
if __name__ == "__main__":
    args = parse_args()
    try:
        run_evaluation(args)
    except KeyboardInterrupt:
        print("\n[evaluate_rag] Interrupted by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[evaluate_rag] Fatal error: {exc}")
        traceback.print_exc()
        sys.exit(1)
