"""
rag_metrics.py
==============
Standalone metric computation functions for the LexiClear RAG evaluation layer.

This module is NEW and ADDITIVE.
It does NOT import from or modify any existing evaluation code.
It calls the existing rag.* modules only in READ-ONLY observer capacity.

Metrics implemented
-------------------
Existing (reproduced faithfully):
  - compute_semantic_similarity   : cosine similarity of sentence embeddings
  - compute_bertscore             : BERTScore P/R/F1
  - compute_qa_correctness        : exact match OR cosine >= 0.70 (threshold unchanged)

New (RAG triad + additional):
  - compute_context_relevance     : embedding cosine(query, each chunk), averaged
  - compute_faithfulness          : LLM-as-judge via Groq
  - compute_answer_relevance      : embedding cosine(question, answer)
  - compute_context_precision     : ratio of top-ranked chunk relevance to overall
  - compute_context_recall        : LLM-as-judge via Groq
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Resolve project root so we can import rag.* without modifying sys.path
# permanently in callers.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _ensure_project_root_in_path() -> None:
    root = str(_PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_project_root_in_path()


# ===========================================================================
# EXISTING METRIC REPRODUCTION
# ===========================================================================

def compute_semantic_similarity(
    expected: str,
    predicted: str,
    model: SentenceTransformer,
) -> float:
    """
    Cosine similarity between sentence-transformer embeddings of expected and
    predicted answers.

    Reproduces the methodology in evaluation/metrics.py exactly:
      model = SentenceTransformer("all-MiniLM-L6-v2")
      similarity = cosine_similarity([emb_expected], [emb_predicted])[0][0]
    """
    emb_expected = model.encode([str(expected)])
    emb_predicted = model.encode([str(predicted)])
    similarity = cosine_similarity(emb_expected, emb_predicted)[0][0]
    return float(similarity)


def compute_bertscore(
    expected_list: list[str],
    predicted_list: list[str],
) -> tuple[list[float], list[float], list[float]]:
    """
    Compute BERTScore for a batch of (expected, predicted) pairs.

    Returns (precision_list, recall_list, f1_list) each as plain floats.

    Reproduces the methodology in evaluation/metrics.py exactly:
      from bert_score import score
      precision, recall, f1 = score(candidates, references, lang="en")
    """
    try:
        from bert_score import score as bert_score_fn
        precision_t, recall_t, f1_t = bert_score_fn(
            predicted_list,
            expected_list,
            lang="en",
            verbose=False,
        )
        precision = [round(float(x), 4) for x in precision_t]
        recall = [round(float(x), 4) for x in recall_t]
        f1 = [round(float(x), 4) for x in f1_t]
        return precision, recall, f1
    except Exception as exc:
        print(f"[rag_metrics] BERTScore failed: {exc}")
        n = len(expected_list)
        return [0.0] * n, [0.0] * n, [0.0] * n


def _normalize_text(text: str) -> str:
    """Normalise text the same way evaluation/metrics.py does."""
    text = str(text).lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_qa_correctness(
    expected: str,
    predicted: str,
    model: SentenceTransformer,
    threshold: float = 0.70,
) -> int:
    """
    Binary QA correctness.

    Reproduces the methodology in evaluation/metrics.py exactly:
      1. Exact match after normalisation  → 1
      2. Cosine similarity >= threshold   → 1
      3. Otherwise                        → 0

    The threshold is 0.70, unchanged from the original implementation.
    (QA Accuracy = 0.1600 confirmed: 4/25 correct.)
    """
    expected_norm = _normalize_text(expected)
    predicted_norm = _normalize_text(predicted)

    if expected_norm == predicted_norm:
        return 1

    emb_exp = model.encode([str(expected)])
    emb_pred = model.encode([str(predicted)])
    sim = cosine_similarity(emb_exp, emb_pred)[0][0]

    return 1 if sim >= threshold else 0


# ===========================================================================
# NEW METRIC: CONTEXT RELEVANCE
# ===========================================================================

def compute_context_relevance(
    question: str,
    retrieved_chunks: list[Any],   # LangChain Document objects
    model: SentenceTransformer,
) -> float:
    """
    Context Relevance: measures whether retrieved chunks are semantically
    relevant to the user's question.

    Method: embedding cosine similarity between query and each chunk's
    page_content, averaged across all chunks.

    Uses the same all-MiniLM-L6-v2 model as the existing evaluation.
    This is semantic relevance (not human-labelled relevance).

    Returns 0.0 if no chunks were retrieved.
    """
    if not retrieved_chunks:
        return 0.0

    query_emb = model.encode([str(question)])
    chunk_texts = [doc.page_content for doc in retrieved_chunks]
    chunk_embs = model.encode(chunk_texts)

    similarities = cosine_similarity(query_emb, chunk_embs)[0]
    return float(np.mean(similarities))


# ===========================================================================
# NEW METRIC: ANSWER RELEVANCE
# ===========================================================================

def compute_answer_relevance(
    question: str,
    answer: str,
    model: SentenceTransformer,
) -> float:
    """
    Answer Relevance: measures whether the generated answer addresses the
    user's question.

    Method: embedding cosine similarity between question and answer.

    This is distinct from:
    - BERTScore F1   (measures token-level overlap with reference)
    - Semantic Similarity (measures match with expected answer)
    - QA Accuracy  (binary correctness)

    Returns a float in [-1, 1] (practically [0, 1] for sensible answers).
    """
    q_emb = model.encode([str(question)])
    a_emb = model.encode([str(answer)])
    return float(cosine_similarity(q_emb, a_emb)[0][0])


# ===========================================================================
# NEW METRIC: CONTEXT PRECISION
# ===========================================================================

def compute_context_precision(
    question: str,
    retrieved_chunks: list[Any],   # LangChain Document objects, in rank order
    model: SentenceTransformer,
) -> float:
    """
    Context Precision: measures whether the most relevant chunks are ranked
    highest in the retrieval results.

    Method:
      1. Compute cosine(query, chunk_i) for each retrieved chunk.
      2. Sort chunks by this relevance score (descending) → ideal ranking.
      3. Compare ideal ranking with actual retrieval order using
         Normalised Discounted Cumulative Gain (NDCG).

    The relevance scores here are the same semantic-similarity values used
    in Context Relevance, but evaluated in rank order.

    Returns 0.0 if fewer than 2 chunks are retrieved (NDCG undefined for 1
    item).
    """
    if len(retrieved_chunks) < 2:
        return 1.0 if retrieved_chunks else 0.0

    query_emb = model.encode([str(question)])
    chunk_texts = [doc.page_content for doc in retrieved_chunks]
    chunk_embs = model.encode(chunk_texts)

    relevance_scores = cosine_similarity(query_emb, chunk_embs)[0]

    # Actual order: relevance_scores[0] is rank-1, [1] is rank-2, ...
    # Ideal order: sorted descending
    ideal_scores = np.sort(relevance_scores)[::-1]

    def dcg(scores: np.ndarray) -> float:
        """Discounted Cumulative Gain."""
        return float(np.sum(
            scores / np.log2(np.arange(2, len(scores) + 2))
        ))

    actual_dcg = dcg(relevance_scores)
    ideal_dcg = dcg(ideal_scores)

    if ideal_dcg == 0.0:
        return 0.0

    return float(actual_dcg / ideal_dcg)


# ===========================================================================
# LLM-AS-JUDGE HELPER
# ===========================================================================

def _call_groq_judge(prompt: str) -> str:
    """
    Call the same Groq model used by LexiClear (openai/gpt-oss-120b)
    with a judge prompt, utilizing automatic multi-API-key rotation and failover.
    Returns the raw text response.
    """
    try:
        from rag.providers.groq_provider import chat_completion
        response = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
            temperature=0.0,
            max_tokens=16,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[rag_metrics] Groq judge call failed: {exc}")
        return "0.5"   # neutral fallback if all retries fail


def _parse_float_from_llm(text: str, fallback: float = 0.5) -> float:
    """Extract the first float in [0, 1] from LLM output."""
    numbers = re.findall(r"\d+\.?\d*", text)
    for num_str in numbers:
        try:
            val = float(num_str)
            if 0.0 <= val <= 1.0:
                return val
        except ValueError:
            continue
    return fallback


# ===========================================================================
# NEW METRIC: FAITHFULNESS
# ===========================================================================

_FAITHFULNESS_PROMPT = """\
You are an objective evaluator assessing whether an AI-generated answer is \
supported by the provided context.

CONTEXT:
{context}

AI ANSWER:
{answer}

Task: Examine every factual claim in the AI ANSWER.
Determine what fraction of those claims are directly supported by the CONTEXT.

Rules:
- A claim is supported if the CONTEXT explicitly states or clearly implies it.
- Penalise unsupported facts, invented clauses, or information absent from the CONTEXT.
- Do NOT penalise hedging language like "the document does not state...".
- If the answer states it cannot find information, that is considered faithful.

Return ONLY a single decimal number between 0.0 and 1.0.
0.0 = no claims are supported.
1.0 = all claims are fully supported by the context.
Do not include any explanation, just the number.
"""


def compute_faithfulness(
    answer: str,
    retrieved_context_text: str,
    use_llm: bool = True,
) -> float:
    """
    Faithfulness: measures whether the AI answer is supported by the retrieved
    context.

    Method: LLM-as-judge using the same Groq model (openai/gpt-oss-120b)
    used by LexiClear itself.

    If use_llm=False (e.g. for unit tests), falls back to embedding cosine
    similarity between answer and context as a rough proxy.

    Returns a float in [0, 1].
    """
    if not answer or not retrieved_context_text:
        return 0.0

    if use_llm:
        prompt = _FAITHFULNESS_PROMPT.format(
            context=retrieved_context_text[:6000],
            answer=answer[:3000],
        )
        raw = _call_groq_judge(prompt)
        return _parse_float_from_llm(raw, fallback=0.5)
    else:
        # Embedding fallback
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        emb_a = model.encode([str(answer)])
        emb_c = model.encode([str(retrieved_context_text[:2000])])
        return float(cosine_similarity(emb_a, emb_c)[0][0])


# ===========================================================================
# NEW METRIC: CONTEXT RECALL
# ===========================================================================

_CONTEXT_RECALL_PROMPT = """\
You are an objective evaluator assessing whether retrieved context contains \
the information needed to answer a question correctly.

EXPECTED ANSWER (ground truth):
{expected_answer}

RETRIEVED CONTEXT:
{context}

Task: Determine what fraction of the information in the EXPECTED ANSWER is \
present in (or inferable from) the RETRIEVED CONTEXT.

Rules:
- Focus on factual content: numbers, names, dates, clauses, conditions.
- A piece of information counts as recalled if the CONTEXT explicitly contains
  or clearly implies it.
- Do NOT penalise extra information in the context.

Return ONLY a single decimal number between 0.0 and 1.0.
0.0 = none of the expected information is in the context.
1.0 = all expected information is present in the context.
Do not include any explanation, just the number.
"""


def compute_context_recall(
    expected_answer: str,
    retrieved_context_text: str,
    use_llm: bool = True,
) -> float:
    """
    Context Recall: measures whether the retrieved context contains the
    information required to answer the question correctly.

    Method: LLM-as-judge using the same Groq model used by LexiClear.

    If use_llm=False, falls back to embedding cosine similarity between
    expected answer and context as a rough proxy.

    Returns a float in [0, 1].
    """
    if not expected_answer or not retrieved_context_text:
        return 0.0

    if use_llm:
        prompt = _CONTEXT_RECALL_PROMPT.format(
            expected_answer=str(expected_answer)[:2000],
            context=retrieved_context_text[:6000],
        )
        raw = _call_groq_judge(prompt)
        return _parse_float_from_llm(raw, fallback=0.5)
    else:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        emb_exp = model.encode([str(expected_answer)])
        emb_ctx = model.encode([str(retrieved_context_text[:2000])])
        return float(cosine_similarity(emb_exp, emb_ctx)[0][0])


# ===========================================================================
# CHUNK METADATA EXTRACTION
# ===========================================================================

def extract_chunk_metadata(doc: Any, rank: int) -> dict:
    """
    Extract metadata from a LangChain Document object.
    Only records fields that are actually present; never invents metadata.
    """
    meta = doc.metadata if hasattr(doc, "metadata") else {}
    record: dict = {"retrieval_rank": rank, "chunk_text": doc.page_content}

    for field in ("source", "page", "chunk_id", "section", "document_type",
                  "title", "file_name", "domain"):
        if field in meta:
            record[field] = meta[field]

    return record


def build_retrieved_context_text(chunks: list[Any]) -> str:
    """
    Concatenate page_content of all retrieved chunks into a single string
    for LLM-judge prompts.
    """
    parts = []
    for i, doc in enumerate(chunks, start=1):
        parts.append(f"[Chunk {i}]\n{doc.page_content}")
    return "\n\n".join(parts)
