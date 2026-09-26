"""
rag_graphs.py
=============
Publication-quality graph generation for the LexiClear RAG evaluation.

This module is NEW and ADDITIVE — it does not modify any existing file.

All graphs are generated from actual evaluation result DataFrames.
No values are hard-coded. If a column is unavailable, the graph is skipped
with a clear warning printed to stdout.

Graph inventory
---------------
1. rag_triad_heatmap.png           — heatmap Q x [CR, Faith, AR]
2. retrieval_generation_quadrant.png — scatter CR vs Faithfulness
3. aggregate_rag_metrics.png        — bar chart new RAG metrics
4. answer_quality_metrics.png       — bar chart existing answer metrics
5. question_faithfulness.png        — per-question faithfulness bar
6. question_context_relevance.png   — per-question context relevance bar
7. question_answer_relevance.png    — per-question answer relevance bar
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap

# Use non-interactive backend so graphs can be generated without a display
matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Shared style constants
# ---------------------------------------------------------------------------
DPI = 200
FONT_FAMILY = "DejaVu Sans"
TITLE_SIZE = 14
LABEL_SIZE = 11
TICK_SIZE = 9
VALUE_SIZE = 8

PALETTE_LOW  = "#d73027"   # red
PALETTE_MID  = "#fee08b"   # yellow
PALETTE_HIGH = "#1a9850"   # green

_RAG_CMAP = LinearSegmentedColormap.from_list(
    "rag_cmap",
    [PALETTE_LOW, PALETTE_MID, PALETTE_HIGH],
)

plt.rcParams.update({
    "font.family": FONT_FAMILY,
    "axes.titlesize": TITLE_SIZE,
    "axes.labelsize": LABEL_SIZE,
    "xtick.labelsize": TICK_SIZE,
    "ytick.labelsize": TICK_SIZE,
    "figure.dpi": DPI,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _has_column(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and df[col].notna().any()


def _question_labels(df: pd.DataFrame) -> list[str]:
    """Short Q-labels: Q1, Q2, …"""
    return [f"Q{i+1}" for i in range(len(df))]


def _save(fig: plt.Figure, path: Path, name: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    fpath = path / name
    fig.savefig(fpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[rag_graphs] Saved: {fpath}")


# ===========================================================================
# GRAPH 1 — RAG Triad Heatmap
# ===========================================================================

def plot_rag_triad_heatmap(
    df: pd.DataFrame,
    output_dir: Path,
) -> Optional[Path]:
    """
    Heatmap: rows = questions, columns = [Context Relevance, Faithfulness,
    Answer Relevance].  Cell values are the actual computed scores.
    """
    required = ["context_relevance", "faithfulness", "answer_relevance"]
    missing = [c for c in required if not _has_column(df, c)]
    if missing:
        print(f"[rag_graphs] Skipping RAG triad heatmap — missing: {missing}")
        return None

    matrix = df[required].values.astype(float)
    q_labels = _question_labels(df)
    col_labels = ["Context Relevance", "Faithfulness", "Answer Relevance"]

    fig_h = max(6, len(df) * 0.35)
    fig, ax = plt.subplots(figsize=(9, fig_h))

    im = ax.imshow(matrix, cmap=_RAG_CMAP, vmin=0.0, vmax=1.0, aspect="auto")

    # Annotate each cell
    for row in range(len(df)):
        for col in range(3):
            val = matrix[row, col]
            color = "black" if 0.35 < val < 0.85 else "white"
            ax.text(
                col, row, f"{val:.2f}",
                ha="center", va="center",
                fontsize=VALUE_SIZE, color=color,
            )

    ax.set_xticks(range(3))
    ax.set_xticklabels(col_labels, fontsize=TICK_SIZE + 1)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(q_labels, fontsize=TICK_SIZE)
    ax.set_title("RAG Triad Evaluation Across Questions", fontsize=TITLE_SIZE, pad=14)

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.03)
    cbar.set_label("Score (0–1)", fontsize=TICK_SIZE)
    cbar.ax.tick_params(labelsize=TICK_SIZE)

    fig.tight_layout()
    _save(fig, output_dir, "rag_triad_heatmap.png")
    return output_dir / "rag_triad_heatmap.png"


# ===========================================================================
# GRAPH 2 — Retrieval vs Generation Scatter
# ===========================================================================

def plot_retrieval_generation_quadrant(
    df: pd.DataFrame,
    output_dir: Path,
) -> Optional[Path]:
    """
    Scatter: X = Context Relevance (retrieval quality),
             Y = Faithfulness (generation groundedness).
    Each point is one question, labelled Q1…QN.
    """
    if not _has_column(df, "context_relevance") or \
       not _has_column(df, "faithfulness"):
        print("[rag_graphs] Skipping quadrant scatter — missing columns.")
        return None

    x = df["context_relevance"].values.astype(float)
    y = df["faithfulness"].values.astype(float)
    q_labels = _question_labels(df)

    fig, ax = plt.subplots(figsize=(9, 7))

    scatter = ax.scatter(
        x, y,
        c=x + y,
        cmap=_RAG_CMAP,
        s=80, zorder=3, edgecolors="grey", linewidths=0.5,
    )

    for i, label in enumerate(q_labels):
        ax.annotate(
            label,
            (x[i], y[i]),
            textcoords="offset points",
            xytext=(5, 4),
            fontsize=6.5,
            color="#333333",
        )

    ax.set_xlabel("Context Relevance (Retrieval Quality)", fontsize=LABEL_SIZE)
    ax.set_ylabel("Faithfulness (Generation Groundedness)", fontsize=LABEL_SIZE)
    ax.set_title("Retrieval vs. Generation Groundedness", fontsize=TITLE_SIZE, pad=12)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.grid(True, alpha=0.3, linestyle="--")

    cb = fig.colorbar(scatter, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("CR + Faithfulness (combined)", fontsize=8)
    cb.ax.tick_params(labelsize=8)

    fig.tight_layout()
    _save(fig, output_dir, "retrieval_generation_quadrant.png")
    return output_dir / "retrieval_generation_quadrant.png"


# ===========================================================================
# GRAPH 3 — Aggregate RAG Metrics Bar Chart
# ===========================================================================

def plot_aggregate_rag_metrics(
    agg: dict,
    output_dir: Path,
) -> Optional[Path]:
    """
    Bar chart of aggregate averages for the five new RAG metrics.
    If a metric is unavailable, a hatched placeholder bar labelled
    'N/A' is shown instead of 0.
    """
    metric_keys = [
        ("context_relevance",  "Context\nRelevance"),
        ("context_precision",  "Context\nPrecision"),
        ("context_recall",     "Context\nRecall"),
        ("faithfulness",       "Faithfulness"),
        ("answer_relevance",   "Answer\nRelevance"),
    ]

    labels, values, available = [], [], []
    for key, label in metric_keys:
        labels.append(label)
        val = agg.get(key)
        values.append(val if val is not None else 0.0)
        available.append(val is not None)

    fig, ax = plt.subplots(figsize=(10, 5))
    bar_colors = [PALETTE_HIGH if a else "#cccccc" for a in available]
    bars = ax.bar(labels, values, color=bar_colors, width=0.55, zorder=3)

    for bar, avail, val in zip(bars, available, values):
        if not avail:
            bar.set_hatch("//")
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                0.02, "N/A",
                ha="center", va="bottom",
                fontsize=TICK_SIZE, color="#555555",
            )
        else:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + 0.015,
                f"{val:.3f}",
                ha="center", va="bottom",
                fontsize=TICK_SIZE, fontweight="bold",
            )

    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score (0–1)", fontsize=LABEL_SIZE)
    ax.set_title("Aggregate RAG Metrics — LexiClear Evaluation", fontsize=TITLE_SIZE, pad=12)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.grid(axis="y", alpha=0.3, linestyle="--", zorder=0)

    fig.tight_layout()
    _save(fig, output_dir, "aggregate_rag_metrics.png")
    return output_dir / "aggregate_rag_metrics.png"


# ===========================================================================
# GRAPH 4 — Existing Answer Quality Metrics Bar Chart
# ===========================================================================

def plot_answer_quality_metrics(
    agg: dict,
    output_dir: Path,
) -> Optional[Path]:
    """
    Bar chart for the five existing answer-quality metrics.
    """
    metric_keys = [
        ("semantic_similarity",  "Semantic\nSimilarity"),
        ("bertscore_precision",  "BERTScore\nPrecision"),
        ("bertscore_recall",     "BERTScore\nRecall"),
        ("bertscore_f1",         "BERTScore\nF1"),
        ("qa_accuracy",          "QA\nAccuracy"),
    ]

    labels, values = [], []
    for key, label in metric_keys:
        labels.append(label)
        values.append(float(agg.get(key, 0.0)))

    bar_color = "#4e79a7"

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, values, color=bar_color, width=0.55, zorder=3)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.012,
            f"{val:.4f}",
            ha="center", va="bottom",
            fontsize=TICK_SIZE, fontweight="bold",
        )

    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score (0–1)", fontsize=LABEL_SIZE)
    ax.set_title(
        "Existing Answer Quality Metrics — LexiClear Evaluation",
        fontsize=TITLE_SIZE, pad=12,
    )
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.grid(axis="y", alpha=0.3, linestyle="--", zorder=0)

    fig.tight_layout()
    _save(fig, output_dir, "answer_quality_metrics.png")
    return output_dir / "answer_quality_metrics.png"


# ===========================================================================
# GRAPH 5 — Question-Level Faithfulness
# ===========================================================================

def plot_question_faithfulness(
    df: pd.DataFrame,
    output_dir: Path,
) -> Optional[Path]:
    """Bar chart: per-question faithfulness score."""
    if not _has_column(df, "faithfulness"):
        print("[rag_graphs] Skipping question faithfulness — column missing.")
        return None
    return _plot_per_question_metric(
        df, "faithfulness",
        "Faithfulness per Question",
        "question_faithfulness.png",
        output_dir,
        color="#e15759",
    )


# ===========================================================================
# GRAPH 6 — Question-Level Context Relevance
# ===========================================================================

def plot_question_context_relevance(
    df: pd.DataFrame,
    output_dir: Path,
) -> Optional[Path]:
    """Bar chart: per-question context relevance score."""
    if not _has_column(df, "context_relevance"):
        print("[rag_graphs] Skipping context relevance chart — column missing.")
        return None
    return _plot_per_question_metric(
        df, "context_relevance",
        "Context Relevance per Question",
        "question_context_relevance.png",
        output_dir,
        color="#f28e2b",
    )


# ===========================================================================
# GRAPH 7 — Question-Level Answer Relevance
# ===========================================================================

def plot_question_answer_relevance(
    df: pd.DataFrame,
    output_dir: Path,
) -> Optional[Path]:
    """Bar chart: per-question answer relevance score."""
    if not _has_column(df, "answer_relevance"):
        print("[rag_graphs] Skipping answer relevance chart — column missing.")
        return None
    return _plot_per_question_metric(
        df, "answer_relevance",
        "Answer Relevance per Question",
        "question_answer_relevance.png",
        output_dir,
        color="#76b7b2",
    )


# ===========================================================================
# Shared per-question bar helper
# ===========================================================================

def _plot_per_question_metric(
    df: pd.DataFrame,
    column: str,
    title: str,
    filename: str,
    output_dir: Path,
    color: str = "#4e79a7",
) -> Path:
    q_labels = _question_labels(df)
    values = df[column].values.astype(float)

    fig_w = max(10, len(df) * 0.55)
    fig, ax = plt.subplots(figsize=(fig_w, 5))

    bars = ax.bar(q_labels, values, color=color, width=0.65, zorder=3)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.015,
            f"{val:.2f}",
            ha="center", va="bottom",
            fontsize=6.5, rotation=0,
        )

    mean_val = float(np.mean(values))
    ax.axhline(mean_val, color="#555555", linestyle="--", linewidth=1.2, zorder=4)
    ax.text(
        len(df) - 0.5, mean_val + 0.02,
        f"mean={mean_val:.3f}",
        ha="right", va="bottom",
        fontsize=8, color="#555555",
    )

    ax.set_ylim(0, 1.15)
    ax.set_xlabel("Question", fontsize=LABEL_SIZE)
    ax.set_ylabel("Score (0–1)", fontsize=LABEL_SIZE)
    ax.set_title(title, fontsize=TITLE_SIZE, pad=12)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.grid(axis="y", alpha=0.3, linestyle="--", zorder=0)

    plt.xticks(rotation=45, ha="right", fontsize=8)
    fig.tight_layout()
    _save(fig, output_dir, filename)
    return output_dir / filename


# ===========================================================================
# Convenience: generate all graphs at once
# ===========================================================================

def generate_all_graphs(
    df: pd.DataFrame,
    agg: dict,
    output_dir: Path,
) -> list[Path]:
    """
    Generate all 7 graphs from the result DataFrame and aggregate dict.
    Returns list of paths to graphs that were successfully generated.
    """
    generated = []

    fns = [
        lambda: plot_rag_triad_heatmap(df, output_dir),
        lambda: plot_retrieval_generation_quadrant(df, output_dir),
        lambda: plot_aggregate_rag_metrics(agg, output_dir),
        lambda: plot_answer_quality_metrics(agg, output_dir),
        lambda: plot_question_faithfulness(df, output_dir),
        lambda: plot_question_context_relevance(df, output_dir),
        lambda: plot_question_answer_relevance(df, output_dir),
    ]

    for fn in fns:
        try:
            result = fn()
            if result is not None:
                generated.append(result)
        except Exception as exc:
            print(f"[rag_graphs] Graph generation error: {exc}")

    return generated
