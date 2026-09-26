"""
rag_report.py
=============
Generates the human-readable Markdown evaluation report for LexiClear.

This module is NEW and ADDITIVE — it does not modify any existing file.

The report includes:
  - Evaluation setup and configuration
  - Metric definitions (with legal-domain disclaimer)
  - Aggregate results
  - Per-question results table
  - RAG triad analysis
  - Failure analysis (pattern-based, not deterministic)
  - Limitations
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Thresholds used ONLY for failure-pattern analysis labels (not for scoring)
# ---------------------------------------------------------------------------
_LOW  = 0.40
_HIGH = 0.65


def _fmt(val: Any, decimals: int = 4) -> str:
    """Format a numeric value or return 'N/A'."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return str(val)


def _metric_row(label: str, val: Any, ref: Optional[float] = None) -> str:
    """One row of the aggregate metrics table."""
    val_str = _fmt(val)
    if ref is not None and val is not None:
        diff = float(val) - ref
        diff_str = f"({diff:+.4f} vs. reference)" if abs(diff) > 0.002 else "(matches reference)"
    else:
        diff_str = ""
    return f"| {label} | {val_str} | {diff_str} |"


# ===========================================================================
# FAILURE ANALYSIS
# ===========================================================================

def _classify_failure(row: pd.Series) -> str:
    """
    Return a short failure-pattern label for one question row.
    Uses soft thresholds — not deterministic classification.
    """
    cr  = row.get("context_relevance")
    fa  = row.get("faithfulness")
    ar  = row.get("answer_relevance")
    qa  = row.get("qa_correct")

    if any(x is None or (isinstance(x, float) and np.isnan(x))
           for x in [cr, fa, ar]):
        return "insufficient data"

    cr, fa, ar = float(cr), float(fa), float(ar)

    if cr < _LOW and fa < _LOW:
        return "possible retrieval failure"
    if cr >= _HIGH and fa < _LOW:
        return "possible generation/grounding failure"
    if fa >= _HIGH and ar < _LOW:
        return "grounded but off-topic response"
    if cr >= _HIGH and fa >= _HIGH and qa == 0:
        return "high retrieval+faithfulness, QA mismatch"
    if cr >= _HIGH and fa >= _HIGH and ar >= _HIGH:
        return "all metrics high"
    return "mixed / no clear pattern"


# ===========================================================================
# MAIN REPORT FUNCTION
# ===========================================================================

def generate_report(
    df: pd.DataFrame,
    agg: dict,
    output_path: Path,
    config: dict,
    graphs_generated: list[Path],
) -> Path:
    """
    Write a Markdown evaluation report.

    Parameters
    ----------
    df            : per-question results DataFrame
    agg           : aggregate metric dictionary
    output_path   : where to write the .md file
    config        : dict with evaluation configuration metadata
    graphs_generated : list of paths to generated graph files
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: list[str] = []
    add = lines.append

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------
    add("# LexiClear RAG Evaluation Report")
    add("")
    add(f"**Generated:** {timestamp}")
    add("")
    add("> **Legal Domain Disclaimer:** This evaluation measures document-grounded "
        "retrieval quality, contextual relevance, response grounding, answer relevance, "
        "and similarity to expected document-derived answers. It does NOT measure legal "
        "validity, legal correctness in an authoritative sense, correctness of court "
        "interpretation, or professional legal advice quality.")
    add("")

    # -----------------------------------------------------------------------
    # 1. Evaluation Setup
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 1. Evaluation Setup")
    add("")
    add("| Parameter | Value |")
    add("|-----------|-------|")
    add(f"| Evaluation timestamp | {timestamp} |")
    add(f"| Dataset file | `{config.get('dataset_file', 'evaluation/evaluation.xlsx')}` |")
    add(f"| Questions in dataset | {config.get('total_questions', 'N/A')} |")
    add(f"| Questions evaluated | {config.get('questions_evaluated', 'N/A')} |")
    add(f"| LLM model | `{config.get('llm_model', 'openai/gpt-oss-120b')}` |")
    add(f"| LLM provider | `{config.get('llm_provider', 'Groq')}` |")
    add(f"| Embedding model | `{config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')}` |")
    add(f"| Document retriever | MMR, k=5, fetch_k=20 (chroma_docs/) |")
    add(f"| Legal retriever | similarity_search, k=3 per domain (chroma_legal/) |")
    add(f"| Chunk size | 800 chars |")
    add(f"| Chunk overlap | 150 chars |")
    add(f"| QA correctness threshold | cosine ≥ 0.70 (unchanged from original) |")
    add(f"| Answer extraction | `## Direct Answer` section only |")
    add(f"| Mode | {config.get('mode', 'live')} |")
    add("")

    # -----------------------------------------------------------------------
    # 2. Document Context Note
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 2. Document Context Note")
    add("")
    doc_note = config.get("document_context_note", "")
    if doc_note:
        add(f"> ⚠️ {doc_note}")
    else:
        add("The evaluation used whichever document was loaded in `chroma_docs/` "
            "at the time of evaluation — the same document the live LexiClear "
            "application would use.")
    add("")

    # -----------------------------------------------------------------------
    # 3. Metric Definitions
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 3. Metric Definitions")
    add("")
    definitions = [
        ("Context Relevance",
         "Measures whether retrieved chunks are semantically relevant to the "
         "user's query. Computed as the mean cosine similarity between the query "
         "embedding and each retrieved chunk embedding (all-MiniLM-L6-v2). "
         "This is *semantic* relevance, not human-labelled relevance."),
        ("Context Precision",
         "Measures whether more-relevant chunks are ranked above less-relevant "
         "chunks. Computed as NDCG (Normalised Discounted Cumulative Gain) over "
         "chunk relevance scores derived from embedding cosine similarity."),
        ("Context Recall",
         "Measures whether the retrieved context contains the information needed "
         "to answer the question. Computed via LLM-as-judge (Groq openai/gpt-oss-120b) "
         "comparing the expected answer against retrieved context."),
        ("Faithfulness",
         "Measures whether the generated answer is supported by the retrieved context. "
         "Computed via LLM-as-judge (Groq openai/gpt-oss-120b). A high score means "
         "claims in the answer are grounded in the context; a low score indicates "
         "possible hallucination or unsupported content."),
        ("Answer Relevance",
         "Measures whether the generated answer addresses the user's question. "
         "Computed as cosine similarity between the question embedding and the "
         "answer embedding (all-MiniLM-L6-v2). Distinct from BERTScore and "
         "Semantic Similarity, which compare to the expected answer."),
        ("Semantic Similarity",
         "Cosine similarity between sentence-transformer embeddings of the "
         "expected answer and the generated answer (all-MiniLM-L6-v2). "
         "Reproduces the existing evaluation/metrics.py methodology."),
        ("BERTScore Precision",
         "Token-level semantic precision between generated and reference answers. "
         "Computed using bert-score library (lang='en')."),
        ("BERTScore Recall",
         "Token-level semantic recall between generated and reference answers."),
        ("BERTScore F1",
         "Harmonic mean of BERTScore Precision and Recall."),
        ("QA Accuracy",
         "Binary correctness: 1 if exact-match after normalisation OR cosine "
         "similarity ≥ 0.70 between expected and generated answer; 0 otherwise. "
         "Reproduces the existing evaluation/metrics.py methodology with "
         "threshold=0.70 unchanged."),
    ]

    for name, defn in definitions:
        add(f"### {name}")
        add("")
        add(defn)
        add("")

    # -----------------------------------------------------------------------
    # 4. Aggregate Results
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 4. Aggregate Results")
    add("")
    add("### New RAG Metrics")
    add("")
    add("| Metric | Score |")
    add("|--------|-------|")
    for key, label in [
        ("context_relevance", "Context Relevance (avg)"),
        ("context_precision", "Context Precision (avg NDCG)"),
        ("context_recall",    "Context Recall (avg)"),
        ("faithfulness",      "Faithfulness (avg)"),
        ("answer_relevance",  "Answer Relevance (avg)"),
    ]:
        add(f"| {label} | {_fmt(agg.get(key))} |")
    add("")

    add("### Existing Answer Quality Metrics")
    add("")
    add("| Metric | New Run | Reference | Match? |")
    add("|--------|---------|-----------|--------|")
    reference = {
        "semantic_similarity": 0.5564,
        "bertscore_precision": 0.8736,
        "bertscore_recall":    0.8883,
        "bertscore_f1":        0.8807,
        "qa_accuracy":         0.1600,
    }
    labels_ref = {
        "semantic_similarity": "Semantic Similarity",
        "bertscore_precision": "BERTScore Precision",
        "bertscore_recall":    "BERTScore Recall",
        "bertscore_f1":        "BERTScore F1",
        "qa_accuracy":         "QA Accuracy",
    }
    for key, label in labels_ref.items():
        val = agg.get(key)
        ref = reference[key]
        val_str = _fmt(val)
        ref_str = _fmt(ref)
        if val is not None:
            try:
                match = "✓ close" if abs(float(val) - ref) < 0.01 else "⚠ differs"
            except (TypeError, ValueError):
                match = "?"
        else:
            match = "N/A"
        add(f"| {label} | {val_str} | {ref_str} | {match} |")
    add("")

    # Explanation if metrics differ
    add("#### Cross-check Note")
    add("")
    add("Reference values are from `evaluation/metrics.txt` (25 questions, "
        "evaluated against the previously loaded document). If the current "
        "run differs materially, this is expected when `chroma_docs/` contains "
        "a different document than was present during the original run.")
    add("")

    # -----------------------------------------------------------------------
    # 5. QA Accuracy Detail
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 5. QA Accuracy Detail")
    add("")
    if "qa_correct" in df.columns:
        total = len(df)
        correct = int(df["qa_correct"].sum())
        incorrect = total - correct
        accuracy = correct / total if total > 0 else 0.0
        add(f"- **Total questions:** {total}")
        add(f"- **Correct:** {correct}")
        add(f"- **Incorrect:** {incorrect}")
        add(f"- **QA Accuracy:** {accuracy:.4f} ({correct}/{total})")
        add("")
        if correct == 4 and total == 25:
            add("> This reproduces the reference: 4/25 = 0.1600 ✓")
        add("")

    # -----------------------------------------------------------------------
    # 6. Per-Question Results
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 6. Per-Question Results")
    add("")

    display_cols = [
        ("question", "Question"),
        ("context_relevance", "CR"),
        ("context_precision", "CP"),
        ("context_recall", "CRec"),
        ("faithfulness", "Faith"),
        ("answer_relevance", "AR"),
        ("semantic_similarity", "SemSim"),
        ("bertscore_f1", "BERT-F1"),
        ("qa_correct", "QA"),
    ]

    available_cols = [(k, l) for k, l in display_cols if k in df.columns]
    header = " | ".join(l for _, l in available_cols)
    separator = " | ".join("---" for _ in available_cols)
    add(f"| Q# | {header} |")
    add(f"|----|-{separator}-|")

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        cells = []
        for key, _ in available_cols:
            val = row.get(key)
            if key == "question":
                cells.append(str(val)[:60] + ("…" if len(str(val)) > 60 else ""))
            elif key == "qa_correct":
                cells.append("✓" if val == 1 else "✗")
            else:
                cells.append(_fmt(val, 3))
        add(f"| Q{i} | " + " | ".join(cells) + " |")
    add("")

    # -----------------------------------------------------------------------
    # 7. RAG Triad Analysis
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 7. RAG Triad Analysis")
    add("")
    cr_avg  = agg.get("context_relevance")
    fa_avg  = agg.get("faithfulness")
    ar_avg  = agg.get("answer_relevance")

    if all(v is not None for v in [cr_avg, fa_avg, ar_avg]):
        cr_avg, fa_avg, ar_avg = float(cr_avg), float(fa_avg), float(ar_avg)
        add(f"- **Average Context Relevance:** {cr_avg:.4f}")
        add(f"- **Average Faithfulness:** {fa_avg:.4f}")
        add(f"- **Average Answer Relevance:** {ar_avg:.4f}")
        add("")

        if cr_avg < _LOW:
            add("> The low average context relevance suggests the retrieved chunks "
                "may not be closely matched to the questions. This is consistent with "
                "a possible retrieval-related issue, particularly if the document "
                "loaded in the vector store does not match the QA dataset.")
        elif cr_avg >= _HIGH and fa_avg < _LOW:
            add("> The high context relevance combined with low faithfulness is "
                "consistent with a possible generation/grounding failure — the model "
                "retrieved relevant content but did not stay grounded in it.")
        elif fa_avg >= _HIGH and ar_avg < _LOW:
            add("> The pattern of high faithfulness with low answer relevance suggests "
                "the model stayed grounded in the context but did not address the "
                "actual question. This may indicate a prompt-following issue.")
        else:
            add("> The three RAG triad metrics show a mixed pattern. Review the "
                "per-question table and graphs for individual question analysis.")
    else:
        add("> One or more RAG triad metrics could not be computed. "
            "See the per-question table for available data.")
    add("")

    # -----------------------------------------------------------------------
    # 8. Failure Analysis
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 8. Failure Analysis")
    add("")
    add("Pattern classification uses soft thresholds "
        f"(low < {_LOW}, high ≥ {_HIGH}) and is **indicative**, not deterministic.")
    add("")

    if all(c in df.columns for c in ["context_relevance", "faithfulness", "answer_relevance"]):
        df = df.copy()
        df["_failure_pattern"] = df.apply(_classify_failure, axis=1)

        pattern_groups: dict[str, list[str]] = {}
        for i, (_, row) in enumerate(df.iterrows(), start=1):
            pattern = row["_failure_pattern"]
            pattern_groups.setdefault(pattern, []).append(f"Q{i}")

        pattern_descriptions = {
            "possible retrieval failure":
                "Low Context Relevance AND Low Faithfulness — "
                "indicates a possible retrieval failure where the retrieved chunks "
                "were not relevant to the question.",
            "possible generation/grounding failure":
                "High Context Relevance BUT Low Faithfulness — "
                "indicates a possible generation/grounding failure where relevant "
                "context was retrieved but the answer was not grounded in it.",
            "grounded but off-topic response":
                "High Faithfulness BUT Low Answer Relevance — "
                "the model stayed grounded in context but did not address "
                "the actual question.",
            "high retrieval+faithfulness, QA mismatch":
                "High Context Relevance, High Faithfulness, but QA incorrect — "
                "investigate expected-answer mismatch or QA threshold calibration.",
            "all metrics high":
                "All three RAG triad metrics are high — strongest performance pattern.",
            "mixed / no clear pattern":
                "No clear failure pattern. Individual review recommended.",
            "insufficient data":
                "One or more metrics were unavailable for this question.",
        }

        for pattern, q_ids in sorted(pattern_groups.items(), key=lambda x: -len(x[1])):
            add(f"### Pattern: {pattern.title()}")
            add("")
            desc = pattern_descriptions.get(pattern, "")
            if desc:
                add(f"*{desc}*")
                add("")
            add(f"**Questions:** {', '.join(q_ids)} ({len(q_ids)} total)")
            add("")
    else:
        add("> Failure analysis requires context_relevance, faithfulness, and "
            "answer_relevance columns. One or more were not available.")
    add("")

    # -----------------------------------------------------------------------
    # 9. Retrieval Configuration Detail
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 9. Retrieval Configuration (from source code)")
    add("")
    add("| Component | Detail |")
    add("|-----------|--------|")
    add("| Document retriever | `rag/retriever.py` → `retrieve_context()` |")
    add("| Search type | MMR (Maximal Marginal Relevance) |")
    add("| k | 5 |")
    add("| fetch_k | 20 |")
    add("| Vector store (docs) | Chroma, persisted at `./chroma_docs/` |")
    add("| Legal retriever | `rag/legal_retriever.py` → `retrieve_legal_context()` |")
    add("| Legal search type | similarity_search |")
    add("| Legal k | 3 per domain |")
    add("| Vector store (legal) | Chroma, persisted at `./chroma_legal/` |")
    add("| Context fusion | `rag/context_fusion.py` → `build_context()` |")
    add("")

    # -----------------------------------------------------------------------
    # 10. Graphs Generated
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 10. Graphs Generated")
    add("")
    if graphs_generated:
        for g in graphs_generated:
            add(f"- `{g.name}`")
    else:
        add("No graphs were generated.")
    add("")

    # -----------------------------------------------------------------------
    # 11. Limitations
    # -----------------------------------------------------------------------
    add("---")
    add("")
    add("## 11. Limitations")
    add("")
    limitations = [
        ("Vector store document mismatch",
         "The QA dataset tests an employment contract. If `chroma_docs/` contains "
         "a different document (e.g., a lease agreement), retrieval and generation "
         "metrics will reflect that mismatch rather than the target document's performance."),
        ("LLM-as-judge variability",
         "Faithfulness and Context Recall are computed via LLM-as-judge using the same "
         "Groq model (openai/gpt-oss-120b). LLM judges can be inconsistent; scores "
         "may vary slightly across runs. Temperature is set to 0.0 for reproducibility."),
        ("Semantic relevance vs. human relevance",
         "Context Relevance and Answer Relevance use embedding cosine similarity, which "
         "captures semantic proximity but not necessarily human-judged topical relevance."),
        ("Small dataset",
         "25 questions limits statistical power. Patterns identified in the failure "
         "analysis should be treated as hypotheses, not conclusions."),
        ("Legal domain scope",
         "This evaluation does not assess legal correctness, legal validity, or the "
         "quality of legal advice. It measures document-grounded retrieval and "
         "generation quality only."),
        ("Context Precision scope",
         "NDCG-based Context Precision measures whether the retriever ranked more "
         "semantically relevant chunks higher. This does not capture whether the "
         "chunks contained the legally correct information."),
    ]

    for title, text in limitations:
        add(f"### {title}")
        add("")
        add(text)
        add("")

    add("---")
    add("")
    add("*End of LexiClear RAG Evaluation Report*")
    add("")

    # Write file
    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    print(f"[rag_report] Report saved: {output_path}")
    return output_path
