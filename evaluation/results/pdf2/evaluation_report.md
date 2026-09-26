# LexiClear RAG Evaluation Report

**Generated:** 2026-09-25 20:44:55

> **Legal Domain Disclaimer:** This evaluation measures document-grounded retrieval quality, contextual relevance, response grounding, answer relevance, and similarity to expected document-derived answers. It does NOT measure legal validity, legal correctness in an authoritative sense, correctness of court interpretation, or professional legal advice quality.

---

## 1. Evaluation Setup

| Parameter | Value |
|-----------|-------|
| Evaluation timestamp | 2026-09-25 20:44:55 |
| Dataset file | `C:\Lexi_Clear\LexiClear\evaluation\evaluation.xlsx` |
| Questions in dataset | 80 |
| Questions evaluated | 80 |
| LLM model | `openai/gpt-oss-120b` |
| LLM provider | `Groq` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Document retriever | MMR, k=5, fetch_k=20 (chroma_docs/) |
| Legal retriever | similarity_search, k=3 per domain (chroma_legal/) |
| Chunk size | 800 chars |
| Chunk overlap | 150 chars |
| QA correctness threshold | cosine ≥ 0.70 (unchanged from original) |
| Answer extraction | `## Direct Answer` section only |
| Mode | fully_live |

---

## 2. Document Context Note

The evaluation used whichever document was loaded in `chroma_docs/` at the time of evaluation — the same document the live LexiClear application would use.

---

## 3. Metric Definitions

### Context Relevance

Measures whether retrieved chunks are semantically relevant to the user's query. Computed as the mean cosine similarity between the query embedding and each retrieved chunk embedding (all-MiniLM-L6-v2). This is *semantic* relevance, not human-labelled relevance.

### Context Precision

Measures whether more-relevant chunks are ranked above less-relevant chunks. Computed as NDCG (Normalised Discounted Cumulative Gain) over chunk relevance scores derived from embedding cosine similarity.

### Context Recall

Measures whether the retrieved context contains the information needed to answer the question. Computed via LLM-as-judge (Groq openai/gpt-oss-120b) comparing the expected answer against retrieved context.

### Faithfulness

Measures whether the generated answer is supported by the retrieved context. Computed via LLM-as-judge (Groq openai/gpt-oss-120b). A high score means claims in the answer are grounded in the context; a low score indicates possible hallucination or unsupported content.

### Answer Relevance

Measures whether the generated answer addresses the user's question. Computed as cosine similarity between the question embedding and the answer embedding (all-MiniLM-L6-v2). Distinct from BERTScore and Semantic Similarity, which compare to the expected answer.

### Semantic Similarity

Cosine similarity between sentence-transformer embeddings of the expected answer and the generated answer (all-MiniLM-L6-v2). Reproduces the existing evaluation/metrics.py methodology.

### BERTScore Precision

Token-level semantic precision between generated and reference answers. Computed using bert-score library (lang='en').

### BERTScore Recall

Token-level semantic recall between generated and reference answers.

### BERTScore F1

Harmonic mean of BERTScore Precision and Recall.

### QA Accuracy

Binary correctness: 1 if exact-match after normalisation OR cosine similarity ≥ 0.70 between expected and generated answer; 0 otherwise. Reproduces the existing evaluation/metrics.py methodology with threshold=0.70 unchanged.

---

## 4. Aggregate Results

### New RAG Metrics

| Metric | Score |
|--------|-------|
| Context Relevance (avg) | 0.4139 |
| Context Precision (avg NDCG) | 0.9823 |
| Context Recall (avg) | 0.5000 |
| Faithfulness (avg) | 0.5000 |
| Answer Relevance (avg) | 0.7400 |

### Existing Answer Quality Metrics

| Metric | New Run | Reference | Match? |
|--------|---------|-----------|--------|
| Semantic Similarity | 0.7971 | 0.5564 | ⚠ differs |
| BERTScore Precision | 0.8706 | 0.8736 | ✓ close |
| BERTScore Recall | 0.9379 | 0.8883 | ⚠ differs |
| BERTScore F1 | 0.9026 | 0.8807 | ⚠ differs |
| QA Accuracy | 0.8000 | 0.1600 | ⚠ differs |

#### Cross-check Note

Reference values are from `evaluation/metrics.txt` (25 questions, evaluated against the previously loaded document). If the current run differs materially, this is expected when `chroma_docs/` contains a different document than was present during the original run.

---

## 5. QA Accuracy Detail

- **Total questions:** 80
- **Correct:** 64
- **Incorrect:** 16
- **QA Accuracy:** 0.8000 (64/80)


---

## 6. Per-Question Results

| Q# | Question | CR | CP | CRec | Faith | AR | SemSim | BERT-F1 | QA |
|----|---- | --- | --- | --- | --- | --- | --- | --- | ----|
| Q1 | What is the name of the document? | 0.310 | 0.823 | 0.500 | 0.500 | 0.555 | 0.941 | 0.918 | ✓ |
| Q2 | Where and on what date is the Deed of Mortgage made? | 0.409 | 1.000 | 0.500 | 0.500 | 0.693 | 0.912 | 0.933 | ✓ |
| Q3 | Who is the mortgagor named in the deed? | 0.488 | 1.000 | 0.500 | 0.500 | 0.772 | 0.792 | 0.867 | ✓ |
| Q4 | Who is the mortgagee named in the deed? | 0.473 | 1.000 | 0.500 | 0.500 | 0.761 | 0.811 | 0.887 | ✓ |
| Q5 | What is the father's name of the mortgagor? | 0.376 | 1.000 | 0.500 | 0.500 | 0.773 | 0.922 | 0.910 | ✓ |
| Q6 | What is the father's name of the mortgagee? | 0.423 | 1.000 | 0.500 | 0.500 | 0.757 | 0.940 | 0.894 | ✓ |
| Q7 | Where does the mortgagor reside? | 0.391 | 1.000 | 0.500 | 0.500 | 0.712 | 0.989 | 0.929 | ✓ |
| Q8 | Where does the mortgagee reside? | 0.421 | 1.000 | 0.500 | 0.500 | 0.593 | 0.990 | 0.930 | ✓ |
| Q9 | How are Rajesh Kumar and Suresh Sharma identified in the dee… | 0.295 | 0.991 | 0.500 | 0.500 | 0.716 | 0.891 | 0.914 | ✓ |
| Q10 | What property is the mortgagor stated to be entitled to? | 0.510 | 1.000 | 0.500 | 0.500 | 0.729 | 0.977 | 0.966 | ✓ |
| Q11 | What amount did the mortgagor request the mortgagee to lend? | 0.516 | 1.000 | 0.500 | 0.500 | 0.790 | 0.858 | 0.899 | ✓ |
| Q12 | What amount did the mortgagee agree to lend? | 0.428 | 1.000 | 0.500 | 0.500 | 0.744 | 0.906 | 0.916 | ✓ |
| Q13 | What is the principal mortgage amount? | 0.391 | 1.000 | 0.500 | 0.500 | 0.726 | 0.935 | 0.948 | ✓ |
| Q14 | When was the mortgage amount paid to the mortgagor? | 0.513 | 1.000 | 0.500 | 0.500 | 0.752 | 0.754 | 0.884 | ✓ |
| Q15 | What does the mortgagor acknowledge regarding receipt of the… | 0.534 | 1.000 | 0.500 | 0.500 | 0.765 | 0.882 | 0.905 | ✓ |
| Q16 | What is the repayment date specified in the deed? | 0.517 | 0.998 | 0.500 | 0.500 | 0.832 | 0.815 | 0.898 | ✓ |
| Q17 | What rate of interest applies to the mortgage amount? | 0.429 | 1.000 | 0.500 | 0.500 | 0.789 | 0.742 | 0.899 | ✓ |
| Q18 | From when is interest charged on the mortgage amount? | 0.428 | 0.998 | 0.500 | 0.500 | 0.791 | 0.892 | 0.926 | ✓ |
| Q19 | How often must interest be paid? | 0.369 | 0.961 | 0.500 | 0.500 | 0.729 | 0.760 | 0.846 | ✓ |
| Q20 | When is the first interest installment due? | 0.420 | 0.953 | 0.500 | 0.500 | 0.855 | 0.946 | 0.940 | ✓ |
| Q21 | On what dates are subsequent interest installments stated to… | 0.447 | 0.948 | 0.500 | 0.500 | 0.791 | 0.695 | 0.895 | ✗ |
| Q22 | Until when must the interest installments continue? | 0.429 | 0.961 | 0.500 | 0.500 | 0.708 | 0.567 | 0.863 | ✗ |
| Q23 | What property is transferred by way of mortgage as security? | 0.415 | 1.000 | 0.500 | 0.500 | 0.691 | 0.892 | 0.929 | ✓ |
| Q24 | What is the purpose of transferring the house by way of mort… | 0.383 | 1.000 | 0.500 | 0.500 | 0.664 | 0.835 | 0.876 | ✓ |
| Q25 | Who is responsible for paying the mortgage amount and intere… | 0.488 | 1.000 | 0.500 | 0.500 | 0.700 | 0.811 | 0.870 | ✓ |
| Q26 | Who is entitled to receive the mortgage amount and interest … | 0.519 | 1.000 | 0.500 | 0.500 | 0.730 | 0.823 | 0.901 | ✓ |
| Q27 | What happens after the mortgage amount and interest are full… | 0.485 | 1.000 | 0.500 | 0.500 | 0.656 | 0.795 | 0.863 | ✓ |
| Q28 | Who bears the cost of reconveyance of the mortgaged house? | 0.460 | 1.000 | 0.500 | 0.500 | 0.743 | 0.789 | 0.897 | ✓ |
| Q29 | To whom may the mortgaged house be reconveyed? | 0.495 | 1.000 | 0.500 | 0.500 | 0.645 | 0.390 | 0.858 | ✗ |
| Q30 | What happens if the mortgagor fails to pay the mortgage amou… | 0.526 | 1.000 | 0.500 | 0.500 | 0.752 | 0.719 | 0.901 | ✓ |
| Q31 | How may the mortgagee recover the mortgage amount after defa… | 0.407 | 1.000 | 0.500 | 0.500 | 0.629 | 0.659 | 0.869 | ✗ |
| Q32 | Through what authority may the mortgaged house be sold after… | 0.421 | 1.000 | 0.500 | 0.500 | 0.788 | 0.614 | 0.901 | ✗ |
| Q33 | What must remain as security until the mortgage amount is pa… | 0.467 | 1.000 | 0.500 | 0.500 | 0.838 | 0.857 | 0.914 | ✓ |
| Q34 | What insurance obligation does the mortgagor have? | 0.485 | 1.000 | 0.500 | 0.500 | 0.715 | 0.820 | 0.885 | ✓ |
| Q35 | In whose joint names must the insurance policy be taken? | 0.370 | 0.963 | 0.500 | 0.500 | 0.728 | 0.967 | 0.955 | ✓ |
| Q36 | How long must the insurance policy be kept in force? | 0.302 | 0.952 | 0.500 | 0.500 | 0.719 | 0.774 | 0.905 | ✓ |
| Q37 | Who must pay the insurance premium under the normal arrangem… | 0.391 | 0.983 | 0.500 | 0.500 | 0.707 | 0.934 | 0.926 | ✓ |
| Q38 | What happens if the mortgagor fails to insure the house? | 0.516 | 1.000 | 0.500 | 0.500 | 0.733 | 0.854 | 0.904 | ✓ |
| Q39 | What happens if the mortgagor fails to keep the insurance po… | 0.527 | 1.000 | 0.500 | 0.500 | 0.778 | 0.850 | 0.904 | ✓ |
| Q40 | What happens to an insurance premium paid by the mortgagee? | 0.486 | 1.000 | 0.500 | 0.500 | 0.756 | 0.799 | 0.936 | ✓ |
| Q41 | When may the mortgagor grant a lease of the mortgaged house? | 0.479 | 1.000 | 0.500 | 0.500 | 0.688 | 0.686 | 0.884 | ✗ |
| Q42 | What form of consent is required before the mortgagor grants… | 0.413 | 0.998 | 0.500 | 0.500 | 0.805 | 0.665 | 0.908 | ✗ |
| Q43 | Can the mortgagor grant a lease without the mortgagee's writ… | 0.417 | 1.000 | 0.500 | 0.500 | 0.826 | 0.639 | 0.893 | ✗ |
| Q44 | Who bears stamp duty for the mortgage deed? | 0.405 | 1.000 | 0.500 | 0.500 | 0.821 | 0.692 | 0.939 | ✗ |
| Q45 | Who bears registration charges for the mortgage deed? | 0.402 | 1.000 | 0.500 | 0.500 | 0.749 | 0.710 | 0.944 | ✓ |
| Q46 | Who bears other out-of-pocket expenses for execution and reg… | 0.416 | 0.981 | 0.500 | 0.500 | 0.621 | 0.501 | 0.896 | ✗ |
| Q47 | Who bears the cost of the mortgagor's solicitor or advocate? | 0.485 | 0.998 | 0.500 | 0.500 | 0.618 | 0.375 | 0.865 | ✗ |
| Q48 | Who bears the cost of the mortgagee's solicitor or advocate? | 0.482 | 0.987 | 0.500 | 0.500 | 0.781 | 0.735 | 0.901 | ✓ |
| Q49 | What expenses are specifically covered by the mortgagor's re… | 0.476 | 1.000 | 0.500 | 0.500 | 0.804 | 0.654 | 0.853 | ✗ |
| Q50 | What type of property is described in the Schedule? | 0.330 | 0.963 | 0.500 | 0.500 | 0.493 | 0.654 | 0.870 | ✗ |
| Q51 | What is the Municipal Number of the scheduled property? | 0.307 | 0.992 | 0.500 | 0.500 | 0.892 | 0.775 | 0.912 | ✓ |
| Q52 | Where is the scheduled property situated? | 0.332 | 1.000 | 0.500 | 0.500 | 0.657 | 0.837 | 0.895 | ✓ |
| Q53 | What is the approximate area of the mortgaged property? | 0.328 | 1.000 | 0.500 | 0.500 | 0.824 | 0.861 | 0.917 | ✓ |
| Q54 | What does the property include in addition to the structure? | 0.280 | 0.986 | 0.500 | 0.500 | 0.689 | 0.923 | 0.935 | ✓ |
| Q55 | What is the northern boundary of the mortgaged property? | 0.358 | 1.000 | 0.500 | 0.500 | 0.764 | 0.784 | 0.930 | ✓ |
| Q56 | What is the southern boundary of the mortgaged property? | 0.361 | 1.000 | 0.500 | 0.500 | 0.776 | 0.756 | 0.921 | ✓ |
| Q57 | What is the eastern boundary of the mortgaged property? | 0.364 | 1.000 | 0.500 | 0.500 | 0.829 | 0.806 | 0.944 | ✓ |
| Q58 | What is the western boundary of the mortgaged property? | 0.353 | 1.000 | 0.500 | 0.500 | 0.748 | 0.807 | 0.928 | ✓ |
| Q59 | Which boundary is identified as the Main Road? | 0.165 | 0.968 | 0.500 | 0.500 | 0.848 | 0.856 | 0.917 | ✓ |
| Q60 | Which boundary is identified as Plot No. 46? | 0.139 | 0.983 | 0.500 | 0.500 | 0.792 | 0.858 | 0.919 | ✓ |
| Q61 | Which boundary is identified as Private Property? | 0.288 | 0.954 | 0.500 | 0.500 | 0.830 | 0.873 | 0.914 | ✓ |
| Q62 | Which boundary is identified as a 30ft Road? | 0.130 | 0.954 | 0.500 | 0.500 | 0.849 | 0.898 | 0.914 | ✓ |
| Q63 | What event causes the mortgagee's right to sell the house to… | 0.428 | 1.000 | 0.500 | 0.500 | 0.735 | 0.705 | 0.944 | ✓ |
| Q64 | What amounts can be recovered from the sale proceeds after d… | 0.298 | 0.968 | 0.500 | 0.500 | 0.540 | 0.609 | 0.851 | ✗ |
| Q65 | Does the mortgage secure only the principal amount or also i… | 0.423 | 1.000 | 0.500 | 0.500 | 0.898 | 0.801 | 0.879 | ✓ |
| Q66 | What condition is attached to the mortgagor's promise to rep… | 0.571 | 1.000 | 0.500 | 0.500 | 0.804 | 0.798 | 0.878 | ✓ |
| Q67 | What is the relationship between the repayment date and the … | 0.400 | 0.981 | 0.500 | 0.500 | 0.705 | 0.823 | 0.871 | ✓ |
| Q68 | What must happen for the mortgagee to reconvey the house? | 0.481 | 1.000 | 0.500 | 0.500 | 0.655 | 0.608 | 0.864 | ✗ |
| Q69 | What does the deed provide regarding the successors of the m… | 0.505 | 1.000 | 0.500 | 0.500 | 0.787 | 0.881 | 0.915 | ✓ |
| Q70 | What does the deed provide regarding the successors of the m… | 0.486 | 1.000 | 0.500 | 0.500 | 0.783 | 0.820 | 0.884 | ✓ |
| Q71 | What months are listed for subsequent quarterly interest ins… | 0.306 | 0.883 | 0.500 | 0.500 | 0.832 | 0.702 | 0.888 | ✓ |
| Q72 | What must the mortgagor do with the insurance policy while t… | 0.561 | 1.000 | 0.500 | 0.500 | 0.837 | 0.804 | 0.905 | ✓ |
| Q73 | Who may insure the property if the mortgagor defaults on ins… | 0.499 | 1.000 | 0.500 | 0.500 | 0.743 | 0.698 | 0.885 | ✗ |
| Q74 | Who signed the deed as the mortgagor? | 0.497 | 1.000 | 0.500 | 0.500 | 0.760 | 0.853 | 0.867 | ✓ |
| Q75 | Who signed the deed as the mortgagee? | 0.462 | 1.000 | 0.500 | 0.500 | 0.760 | 0.867 | 0.885 | ✓ |
| Q76 | Who is listed as the first witness? | 0.247 | 0.732 | 0.500 | 0.500 | 0.672 | 0.968 | 0.954 | ✓ |
| Q77 | Who is listed as the second witness? | 0.262 | 0.759 | 0.500 | 0.500 | 0.659 | 0.922 | 0.935 | ✓ |
| Q78 | What is the principal financial obligation created by the de… | 0.445 | 1.000 | 0.500 | 0.500 | 0.660 | 0.778 | 0.890 | ✓ |
| Q79 | What is the stated duration between execution and the repaym… | 0.462 | 0.969 | 0.500 | 0.500 | 0.547 | 0.800 | 0.875 | ✓ |
| Q80 | What property identifier connects the mortgage terms with th… | 0.403 | 1.000 | 0.500 | 0.500 | 0.814 | 0.884 | 0.878 | ✓ |

---

## 7. RAG Triad Analysis

- **Average Context Relevance:** 0.4139
- **Average Faithfulness:** 0.5000
- **Average Answer Relevance:** 0.7400

> The three RAG triad metrics show a mixed pattern. Review the per-question table and graphs for individual question analysis.

---

## 8. Failure Analysis

Pattern classification uses soft thresholds (low < 0.4, high ≥ 0.65) and is **indicative**, not deterministic.

### Pattern: Mixed / No Clear Pattern

*No clear failure pattern. Individual review recommended.*

**Questions:** Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40, Q41, Q42, Q43, Q44, Q45, Q46, Q47, Q48, Q49, Q50, Q51, Q52, Q53, Q54, Q55, Q56, Q57, Q58, Q59, Q60, Q61, Q62, Q63, Q64, Q65, Q66, Q67, Q68, Q69, Q70, Q71, Q72, Q73, Q74, Q75, Q76, Q77, Q78, Q79, Q80 (80 total)


---

## 9. Retrieval Configuration (from source code)

| Component | Detail |
|-----------|--------|
| Document retriever | `rag/retriever.py` → `retrieve_context()` |
| Search type | MMR (Maximal Marginal Relevance) |
| k | 5 |
| fetch_k | 20 |
| Vector store (docs) | Chroma, persisted at `./chroma_docs/` |
| Legal retriever | `rag/legal_retriever.py` → `retrieve_legal_context()` |
| Legal search type | similarity_search |
| Legal k | 3 per domain |
| Vector store (legal) | Chroma, persisted at `./chroma_legal/` |
| Context fusion | `rag/context_fusion.py` → `build_context()` |

---

## 10. Graphs Generated

- `rag_triad_heatmap.png`
- `retrieval_generation_quadrant.png`
- `aggregate_rag_metrics.png`
- `answer_quality_metrics.png`
- `question_faithfulness.png`
- `question_context_relevance.png`
- `question_answer_relevance.png`

---

## 11. Limitations

### Vector store document mismatch

The QA dataset tests an employment contract. If `chroma_docs/` contains a different document (e.g., a lease agreement), retrieval and generation metrics will reflect that mismatch rather than the target document's performance.

### LLM-as-judge variability

Faithfulness and Context Recall are computed via LLM-as-judge using the same Groq model (openai/gpt-oss-120b). LLM judges can be inconsistent; scores may vary slightly across runs. Temperature is set to 0.0 for reproducibility.

### Semantic relevance vs. human relevance

Context Relevance and Answer Relevance use embedding cosine similarity, which captures semantic proximity but not necessarily human-judged topical relevance.

### Small dataset

25 questions limits statistical power. Patterns identified in the failure analysis should be treated as hypotheses, not conclusions.

### Legal domain scope

This evaluation does not assess legal correctness, legal validity, or the quality of legal advice. It measures document-grounded retrieval and generation quality only.

### Context Precision scope

NDCG-based Context Precision measures whether the retriever ranked more semantically relevant chunks higher. This does not capture whether the chunks contained the legally correct information.

---

*End of LexiClear RAG Evaluation Report*
