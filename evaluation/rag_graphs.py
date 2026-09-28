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
    Answer Relevance]. Cell values are the actual computed scores.

    The figure size is optimized for inclusion in an A4 project report:
    all evaluated questions remain visible while keeping the numerical
    cell values readable.
    """
    required = ["context_relevance", "faithfulness", "answer_relevance"]
    missing = [c for c in required if not _has_column(df, c)]

    if missing:
        print(f"[rag_graphs] Skipping RAG triad heatmap — missing: {missing}")
        return None

    matrix = df[required].values.astype(float)
    q_labels = _question_labels(df)
    col_labels = [
        "Context Relevance",
        "Faithfulness",
        "Answer Relevance",
    ]

    # ---------------------------------------------------------------
    # Compact A4-friendly layout
    # ---------------------------------------------------------------
    # The previous implementation used 0.35 inch per question.
    # For 80 questions this produced a ~28 inch tall image.
    #
    # A fixed 8.4 inch height keeps all 80 rows while making the
    # resulting image suitable for insertion into an A4 report.
    # The values remain visible because the annotation and tick
    # sizes are adjusted locally for this dense graph.
    # ---------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.6, 8.4))

    im = ax.imshow(
        matrix,
        cmap=_RAG_CMAP,
        vmin=0.0,
        vmax=1.0,
        aspect="auto",
        interpolation="nearest",
    )

    # ---------------------------------------------------------------
    # Annotate every cell with the actual metric value
    # ---------------------------------------------------------------
    heatmap_value_size = 5.2

    for row in range(len(df)):
        for col in range(3):
            val = matrix[row, col]

            # White text on darker cells and black text on lighter
            # cells to preserve readability across the colour scale.
            color = "black" if 0.35 < val < 0.85 else "white"

            ax.text(
                col,
                row,
                f"{val:.2f}",
                ha="center",
                va="center",
                fontsize=heatmap_value_size,
                color=color,
            )

    # ---------------------------------------------------------------
    # X-axis: three RAG metrics
    # ---------------------------------------------------------------
    ax.set_xticks(range(3))
    ax.set_xticklabels(
        col_labels,
        fontsize=7,
    )

    # ---------------------------------------------------------------
    # Y-axis: all evaluated questions
    # ---------------------------------------------------------------
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(
        q_labels,
        fontsize=6,
    )

    ax.tick_params(
        axis="x",
        pad=3,
        length=3,
    )

    ax.tick_params(
        axis="y",
        pad=2,
        length=3,
    )

    # ---------------------------------------------------------------
    # Title
    # ---------------------------------------------------------------
    ax.set_title(
        "RAG Triad Evaluation Across Questions",
        fontsize=10,
        pad=8,
    )

    # ---------------------------------------------------------------
    # Colour scale
    # ---------------------------------------------------------------
    cbar = fig.colorbar(
        im,
        ax=ax,
        fraction=0.025,
        pad=0.02,
    )

    cbar.set_label(
        "Score (0–1)",
        fontsize=6.5,
    )

    cbar.ax.tick_params(
        labelsize=6,
    )

    # ---------------------------------------------------------------
    # Layout
    # ---------------------------------------------------------------
    fig.subplots_adjust(
        left=0.12,
        right=0.91,
        top=0.95,
        bottom=0.08,
    )

    _save(
        fig,
        output_dir,
        "rag_triad_heatmap.png",
    )

    return output_dir / "rag_triad_heatmap.png"


# ===========================================================================
# GRAPH 2 — Retrieval vs Answer Relevance Scatter
# ===========================================================================

def plot_retrieval_generation_quadrant(
    df: pd.DataFrame,
    output_dir: Path,
) -> Optional[Path]:
    """
    Scatter plot showing the relationship between:

        X-axis = Context Relevance
        Y-axis = Answer Relevance

    Each point represents one evaluated question.

    Both metrics are normalized to the same 0–1 scale used by the
    RAG Triad heatmap. No values are modified or artificially generated.
    """

    required = ["context_relevance", "answer_relevance"]

    missing = [c for c in required if not _has_column(df, c)]

    if missing:
        print(
            "[rag_graphs] Skipping retrieval-vs-answer scatter "
            f"— missing columns: {missing}"
        )
        return None

    # -----------------------------------------------------------------------
    # Read the actual per-question metric values
    # -----------------------------------------------------------------------

    x = df["context_relevance"].astype(float).to_numpy()
    y = df["answer_relevance"].astype(float).to_numpy()

    q_labels = _question_labels(df)

    # -----------------------------------------------------------------------
    # Remove rows where either metric is unavailable.
    # This does NOT alter valid metric values.
    # -----------------------------------------------------------------------

    valid = np.isfinite(x) & np.isfinite(y)

    x = x[valid]
    y = y[valid]

    labels = [
        label
        for label, is_valid in zip(q_labels, valid)
        if is_valid
    ]

    if len(x) == 0:
        print(
            "[rag_graphs] Skipping retrieval-vs-answer scatter "
            "— no valid metric values."
        )
        return None

    # -----------------------------------------------------------------------
    # Combined score is ONLY used for point colouring.
    # It does not change either metric plotted on the axes.
    # -----------------------------------------------------------------------

    combined_score = (x + y) / 2.0

    # -----------------------------------------------------------------------
    # Figure
    #
    # Fixed 0–1 axes make this directly comparable with the RAG heatmap.
    # -----------------------------------------------------------------------

    fig, ax = plt.subplots(figsize=(9, 7))

    scatter = ax.scatter(
        x,
        y,
        c=combined_score,
        cmap=_RAG_CMAP,
        vmin=0.0,
        vmax=1.0,
        s=75,
        alpha=0.85,
        zorder=3,
        edgecolors="grey",
        linewidths=0.5,
    )

    # -----------------------------------------------------------------------
    # Question labels
    # -----------------------------------------------------------------------

    for i, label in enumerate(labels):
        ax.annotate(
            label,
            (x[i], y[i]),
            textcoords="offset points",
            xytext=(5, 4),
            fontsize=6.5,
            color="#333333",
        )

    # -----------------------------------------------------------------------
    # Axes
    #
    # IMPORTANT:
    # Both are explicitly 0–1, exactly like the heatmap.
    # -----------------------------------------------------------------------

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)

    ax.set_xlabel(
        "Context Relevance (Retrieval Quality)",
        fontsize=LABEL_SIZE,
    )

    ax.set_ylabel(
        "Answer Relevance (Answer Quality)",
        fontsize=LABEL_SIZE,
    )

    ax.set_title(
        "Retrieval Quality vs. Answer Relevance",
        fontsize=TITLE_SIZE,
        pad=12,
    )

    # -----------------------------------------------------------------------
    # Tick scale: 0.0 → 1.0 in increments of 0.1
    # -----------------------------------------------------------------------

    ax.xaxis.set_major_locator(
        ticker.MultipleLocator(0.1)
    )

    ax.yaxis.set_major_locator(
        ticker.MultipleLocator(0.1)
    )

    ax.xaxis.set_major_formatter(
        ticker.FormatStrFormatter("%.1f")
    )

    ax.yaxis.set_major_formatter(
        ticker.FormatStrFormatter("%.1f")
    )

    # -----------------------------------------------------------------------
    # Grid
    # -----------------------------------------------------------------------

    ax.grid(
        True,
        alpha=0.3,
        linestyle="--",
        zorder=0,
    )

    # -----------------------------------------------------------------------
    # Reference lines at the dataset means
    #
    # These are descriptive only and help identify questions above/below
    # the average retrieval and answer-relevance scores.
    # -----------------------------------------------------------------------

    mean_x = float(np.mean(x))
    mean_y = float(np.mean(y))

    ax.axvline(
        mean_x,
        color="#555555",
        linestyle=":",
        linewidth=1.1,
        zorder=2,
    )

    ax.axhline(
        mean_y,
        color="#555555",
        linestyle=":",
        linewidth=1.1,
        zorder=2,
    )

    # -----------------------------------------------------------------------
    # Mean labels
    # -----------------------------------------------------------------------

    ax.text(
        mean_x + 0.01,
        0.02,
        f"mean CR = {mean_x:.3f}",
        fontsize=7.5,
        color="#555555",
        rotation=90,
        va="bottom",
    )

    ax.text(
        0.02,
        mean_y + 0.01,
        f"mean AR = {mean_y:.3f}",
        fontsize=7.5,
        color="#555555",
        ha="left",
        va="bottom",
    )

    # -----------------------------------------------------------------------
    # Colour bar
    #
    # Same 0–1 scale as the heatmap.
    # -----------------------------------------------------------------------

    cb = fig.colorbar(
        scatter,
        ax=ax,
        fraction=0.025,
        pad=0.02,
    )

    cb.set_label(
        "Combined Score (CR + AR) / 2",
        fontsize=8,
    )

    cb.ax.tick_params(
        labelsize=8,
    )

    cb.set_ticks(
        np.arange(0.0, 1.01, 0.1)
    )

    # -----------------------------------------------------------------------
    # Layout and save
    # -----------------------------------------------------------------------

    fig.tight_layout()

    _save(
        fig,
        output_dir,
        "retrieval_generation_quadrant.png",
    )

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
    """
    Generate a compact, report-friendly per-question metric graph.

    The graph is deliberately kept at a fixed size so that datasets with
    many questions (e.g. 80 questions) do not produce extremely wide images.

    Metric values are NOT changed or rescaled. Only the visual presentation
    is modified.
    """

    q_labels = _question_labels(df)
    values = df[column].values.astype(float)

    # -----------------------------------------------------------------------
    # FIXED FIGURE SIZE
    #
    # Previously:
    #     fig_w = max(10, len(df) * 0.55)
    #
    # For 80 questions this produced a ~44-inch-wide figure.
    #
    # Fixed dimensions make the graph suitable for direct insertion into
    # the report while keeping all 80 questions visible.
    # -----------------------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(10, 4.8),
        dpi=200,
    )

    x_positions = np.arange(len(df))

    bars = ax.bar(
        x_positions,
        values,
        color=color,
        width=0.72,
        zorder=3,
    )

    # -----------------------------------------------------------------------
    # VALUE LABELS
    #
    # Values are retained for every question.
    # Smaller font is used so that 80 values remain visible.
    # -----------------------------------------------------------------------

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            min(val + 0.025, 1.105),
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=4.5,
            rotation=90,
            clip_on=False,
        )

    # -----------------------------------------------------------------------
    # DATASET MEAN
    # -----------------------------------------------------------------------

    mean_val = float(np.mean(values))

    ax.axhline(
        mean_val,
        color="#555555",
        linestyle="--",
        linewidth=1.0,
        zorder=4,
    )

    ax.text(
        len(df) - 1,
        min(mean_val + 0.025, 1.11),
        f"mean = {mean_val:.3f}",
        ha="right",
        va="bottom",
        fontsize=6.5,
        color="#555555",
        backgroundcolor="white",
    )

    # -----------------------------------------------------------------------
    # AXES
    # -----------------------------------------------------------------------

    ax.set_ylim(0, 1.15)

    ax.set_xlim(-0.8, len(df) - 0.2)

    ax.set_xlabel(
        "Question",
        fontsize=LABEL_SIZE,
    )

    ax.set_ylabel(
        "Score (0–1)",
        fontsize=LABEL_SIZE,
    )

    ax.set_title(
        title,
        fontsize=TITLE_SIZE,
        pad=8,
    )

    # -----------------------------------------------------------------------
    # Y-AXIS SCALE
    #
    # Same 0–1 interpretation as the RAG heatmap.
    # -----------------------------------------------------------------------

    ax.yaxis.set_major_locator(
        ticker.MultipleLocator(0.1)
    )

    ax.yaxis.set_major_formatter(
        ticker.FormatStrFormatter("%.1f")
    )

    # -----------------------------------------------------------------------
    # X-AXIS
    #
    # Keep all 80 question positions, but use compact labels.
    # -----------------------------------------------------------------------

    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        q_labels,
        rotation=90,
        fontsize=5,
        ha="center",
    )

    # -----------------------------------------------------------------------
    # GRID
    # -----------------------------------------------------------------------

    ax.grid(
        axis="y",
        alpha=0.25,
        linestyle="--",
        linewidth=0.6,
        zorder=0,
    )

    # Keep the graph visually clean.
    ax.set_axisbelow(True)

    # -----------------------------------------------------------------------
    # COMPACT LAYOUT
    # -----------------------------------------------------------------------

    fig.tight_layout(
        pad=0.8,
    )

    # -----------------------------------------------------------------------
    # SAVE
    # -----------------------------------------------------------------------

    _save(
        fig,
        output_dir,
        filename,
    )

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
