# LexiClear RAG Evaluation Report

**Generated:** 2026-09-23 21:59:51

> **Legal Domain Disclaimer:** This evaluation measures document-grounded retrieval quality, contextual relevance, response grounding, answer relevance, and similarity to expected document-derived answers. It does NOT measure legal validity, legal correctness in an authoritative sense, correctness of court interpretation, or professional legal advice quality.

---

## 1. Evaluation Setup

| Parameter | Value |
|-----------|-------|
| Evaluation timestamp | 2026-09-23 21:59:51 |
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
| Context Relevance (avg) | 0.3251 |
| Context Precision (avg NDCG) | 0.8934 |
| Context Recall (avg) | 0.5000 |
| Faithfulness (avg) | 0.5000 |
| Answer Relevance (avg) | 0.6142 |

### Existing Answer Quality Metrics

| Metric | New Run | Reference | Match? |
|--------|---------|-----------|--------|
| Semantic Similarity | 0.5039 | 0.5564 | ⚠ differs |
| BERTScore Precision | 0.8698 | 0.8736 | ✓ close |
| BERTScore Recall | 0.8828 | 0.8883 | ✓ close |
| BERTScore F1 | 0.8761 | 0.8807 | ✓ close |
| QA Accuracy | 0.0625 | 0.1600 | ⚠ differs |

#### Cross-check Note

Reference values are from `evaluation/metrics.txt` (25 questions, evaluated against the previously loaded document). If the current run differs materially, this is expected when `chroma_docs/` contains a different document than was present during the original run.

---

## 5. QA Accuracy Detail

- **Total questions:** 80
- **Correct:** 5
- **Incorrect:** 75
- **QA Accuracy:** 0.0625 (5/80)


---

## 6. Per-Question Results

| Q# | Question | CR | CP | CRec | Faith | AR | SemSim | BERT-F1 | QA |
|----|---- | --- | --- | --- | --- | --- | --- | --- | ----|
| Q1 | What position is the employee appointed to? | 0.363 | 0.861 | 0.500 | 0.500 | 0.579 | 0.453 | 0.894 | ✗ |
| Q2 | How long is the probationary period? | 0.307 | 0.881 | 0.500 | 0.500 | 0.560 | 0.572 | 0.898 | ✗ |
| Q3 | Can the company extend the probationary period? | 0.355 | 0.870 | 0.500 | 0.500 | 0.694 | 0.657 | 0.879 | ✗ |
| Q4 | Where is the employee initially stationed? | 0.266 | 0.997 | 0.500 | 0.500 | 0.591 | 0.469 | 0.895 | ✗ |
| Q5 | Can the company transfer the employee to another branch? | 0.250 | 0.938 | 0.500 | 0.500 | 0.660 | 0.472 | 0.873 | ✗ |
| Q6 | Can the employee be required to work outside the company's p… | 0.253 | 0.993 | 0.500 | 0.500 | 0.765 | 0.659 | 0.894 | ✗ |
| Q7 | Who can assign duties and responsibilities to the employee? | 0.362 | 0.856 | 0.500 | 0.500 | 0.470 | 0.383 | 0.870 | ✗ |
| Q8 | Must the employee follow company policies and applicable law… | 0.291 | 0.915 | 0.500 | 0.500 | 0.677 | 0.620 | 0.887 | ✗ |
| Q9 | Can the employee sign company documents without written cons… | 0.313 | 0.877 | 0.500 | 0.500 | 0.760 | 0.729 | 0.898 | ✓ |
| Q10 | Can the company modify its rules and regulations? | 0.320 | 0.965 | 0.500 | 0.500 | 0.543 | 0.463 | 0.868 | ✗ |
| Q11 | Where will arbitration proceedings be held? | 0.447 | 0.790 | 0.500 | 0.500 | 0.581 | 0.439 | 0.870 | ✗ |
| Q12 | Who is appointed as the sole arbitrator? | 0.446 | 0.787 | 0.500 | 0.500 | 0.416 | 0.311 | 0.868 | ✗ |
| Q13 | In which language will the arbitration proceedings be conduc… | 0.456 | 0.788 | 0.500 | 0.500 | 0.677 | 0.644 | 0.875 | ✗ |
| Q14 | What is the employee's annual CTC? | 0.255 | 0.867 | 0.500 | 0.500 | 0.641 | 0.512 | 0.846 | ✗ |
| Q15 | Can the employee disclose confidential company information? | 0.236 | 0.732 | 0.500 | 0.500 | 0.730 | 0.720 | 0.864 | ✓ |
| Q16 | Who owns intellectual property created by the employee durin… | 0.330 | 0.941 | 0.500 | 0.500 | 0.712 | 0.620 | 0.893 | ✗ |
| Q17 | What must the employee do with company documents after termi… | 0.349 | 0.957 | 0.500 | 0.500 | 0.638 | 0.473 | 0.866 | ✗ |
| Q18 | How long does the non-compete restriction apply after employ… | 0.233 | 0.788 | 0.500 | 0.500 | 0.663 | 0.484 | 0.852 | ✗ |
| Q19 | Can the employee directly or indirectly contact the company'… | 0.195 | 0.805 | 0.500 | 0.500 | 0.343 | 0.406 | 0.888 | ✗ |
| Q20 | What notice must the employee give to terminate the employme… | 0.398 | 0.929 | 0.500 | 0.500 | 0.685 | 0.597 | 0.865 | ✗ |
| Q21 | Can the employer terminate the employee immediately without … | 0.255 | 0.924 | 0.500 | 0.500 | 0.632 | 0.625 | 0.881 | ✗ |
| Q22 | What is the penalty for leaving the company before completin… | 0.315 | 0.942 | 0.500 | 0.500 | 0.756 | 0.397 | 0.874 | ✗ |
| Q23 | Can the company recover training expenses if the employee re… | 0.245 | 0.998 | 0.500 | 0.500 | 0.782 | 0.792 | 0.906 | ✓ |
| Q24 | Is severance pay provided if the employee is terminated for … | 0.303 | 0.878 | 0.500 | 0.500 | 0.779 | 0.793 | 0.922 | ✓ |
| Q25 | What law governs the employment agreement? | 0.378 | 0.845 | 0.500 | 0.500 | 0.675 | 0.498 | 0.875 | ✗ |
| Q26 | What is the date and place where the Employment Agreement is… | 0.371 | 0.909 | 0.500 | 0.500 | 0.566 | 0.371 | 0.852 | ✗ |
| Q27 | What is the registered office address of the Employer? | 0.243 | 0.933 | 0.500 | 0.500 | 0.579 | 0.375 | 0.834 | ✗ |
| Q28 | What is the name of the Employer? | 0.268 | 0.882 | 0.500 | 0.500 | 0.432 | 0.306 | 0.855 | ✗ |
| Q29 | What is the name of the Employee? | 0.295 | 0.882 | 0.500 | 0.500 | 0.566 | 0.382 | 0.852 | ✗ |
| Q30 | What is the Employee's residential address stated in the agr… | 0.434 | 0.999 | 0.500 | 0.500 | 0.632 | 0.314 | 0.800 | ✗ |
| Q31 | What may happen if the employee's work performance has not m… | 0.231 | 0.878 | 0.500 | 0.500 | 0.664 | 0.601 | 0.902 | ✗ |
| Q32 | What type of employee status may the employee receive after … | 0.306 | 0.938 | 0.500 | 0.500 | 0.642 | 0.573 | 0.897 | ✗ |
| Q33 | When does the employee become eligible for most company bene… | 0.228 | 0.885 | 0.500 | 0.500 | 0.493 | 0.377 | 0.891 | ✗ |
| Q34 | What standards is the employee expected to maintain after co… | 0.295 | 0.954 | 0.500 | 0.500 | 0.631 | 0.310 | 0.891 | ✗ |
| Q35 | Can the company transfer the employee to a future branch or … | 0.292 | 0.944 | 0.500 | 0.500 | 0.675 | 0.586 | 0.888 | ✗ |
| Q36 | What is the employee required to devote to the performance o… | 0.318 | 0.787 | 0.500 | 0.500 | 0.505 | 0.376 | 0.882 | ✗ |
| Q37 | Whose instructions must the employee follow in performing as… | 0.333 | 0.873 | 0.500 | 0.500 | 0.505 | 0.429 | 0.869 | ✗ |
| Q38 | What standard of conduct is required regarding the company's… | 0.343 | 0.927 | 0.500 | 0.500 | 0.373 | 0.332 | 0.839 | ✗ |
| Q39 | To whom does the employee directly report according to the a… | 0.374 | 0.891 | 0.500 | 0.500 | 0.406 | 0.296 | 0.874 | ✗ |
| Q40 | Can the employee engage in activities outside the scope of e… | 0.275 | 0.980 | 0.500 | 0.500 | 0.774 | 0.698 | 0.909 | ✗ |
| Q41 | What happens if the employee signs documents or commits on b… | 0.405 | 0.943 | 0.500 | 0.500 | 0.651 | 0.487 | 0.873 | ✗ |
| Q42 | Who is responsible for the employee's day-to-day management? | 0.298 | 0.844 | 0.500 | 0.500 | 0.723 | 0.568 | 0.856 | ✗ |
| Q43 | How are changes to the Company's rules and regulations made … | 0.346 | 0.964 | 0.500 | 0.500 | 0.521 | 0.352 | 0.855 | ✗ |
| Q44 | What happens if a claim, dispute, or difference arises conce… | 0.374 | 0.835 | 0.500 | 0.500 | 0.514 | 0.198 | 0.834 | ✗ |
| Q45 | Under which Act is the arbitration to be conducted? | 0.508 | 0.798 | 0.500 | 0.500 | 0.581 | 0.562 | 0.860 | ✗ |
| Q46 | What is the status of the arbitral award under the agreement… | 0.477 | 0.763 | 0.500 | 0.500 | 0.633 | 0.429 | 0.872 | ✗ |
| Q47 | What does the agreement state about salary if the employee f… | 0.298 | 0.900 | 0.500 | 0.500 | 0.671 | 0.695 | 0.915 | ✗ |
| Q48 | What types of company information are covered by the confide… | 0.282 | 0.770 | 0.500 | 0.500 | 0.580 | 0.519 | 0.867 | ✗ |
| Q49 | For what purpose may the employee use confidential company i… | 0.259 | 0.774 | 0.500 | 0.500 | 0.718 | 0.621 | 0.884 | ✗ |
| Q50 | What must the employee do to safeguard the Company's interes… | 0.305 | 0.880 | 0.500 | 0.500 | 0.379 | 0.383 | 0.878 | ✗ |
| Q51 | What happens to intellectual property created during the cou… | 0.284 | 0.945 | 0.500 | 0.500 | 0.615 | 0.536 | 0.878 | ✗ |
| Q52 | What does the agreement state about the Company's source cod… | 0.293 | 0.899 | 0.500 | 0.500 | 0.633 | 0.602 | 0.867 | ✗ |
| Q53 | What action may the Company take if the employee contravenes… | 0.327 | 0.978 | 0.500 | 0.500 | 0.530 | 0.345 | 0.856 | ✗ |
| Q54 | What items issued to the employee must be kept in safe custo… | 0.331 | 0.995 | 0.500 | 0.500 | 0.624 | 0.572 | 0.881 | ✗ |
| Q55 | When must the employee return company-issued items? | 0.295 | 0.962 | 0.500 | 0.500 | 0.693 | 0.696 | 0.923 | ✗ |
| Q56 | What may happen if the employee contravenes the non-compete … | 0.288 | 0.908 | 0.500 | 0.500 | 0.724 | 0.341 | 0.842 | ✗ |
| Q57 | How is the Company's client described in the client-restrict… | 0.340 | 0.852 | 0.500 | 0.500 | 0.655 | 0.476 | 0.880 | ✗ |
| Q58 | What consequence is stated for doing personal work or work f… | 0.260 | 0.892 | 0.500 | 0.500 | 0.631 | 0.558 | 0.907 | ✗ |
| Q59 | What does the Employment Agreement supersede regarding durat… | 0.386 | 0.900 | 0.500 | 0.500 | 0.689 | 0.533 | 0.885 | ✗ |
| Q60 | What happens to the employee's salary during the notice peri… | 0.359 | 0.928 | 0.500 | 0.500 | 0.537 | 0.625 | 0.898 | ✗ |
| Q61 | When is severance pay not provided under the agreement? | 0.345 | 0.938 | 0.500 | 0.500 | 0.785 | 0.749 | 0.872 | ✓ |
| Q62 | What happens if the employee commits an offence punishable u… | 0.326 | 0.853 | 0.500 | 0.500 | 0.613 | 0.605 | 0.876 | ✗ |
| Q63 | What recovery right does the Employer have if the employee c… | 0.256 | 0.906 | 0.500 | 0.500 | 0.547 | 0.513 | 0.855 | ✗ |
| Q64 | What training-related recovery right does the Company have? | 0.179 | 0.863 | 0.500 | 0.500 | 0.615 | 0.487 | 0.857 | ✗ |
| Q65 | What is one ground listed for termination involving dishones… | 0.344 | 0.879 | 0.500 | 0.500 | 0.649 | 0.614 | 0.877 | ✗ |
| Q66 | What happens if the employee commits a material breach of th… | 0.353 | 0.907 | 0.500 | 0.500 | 0.585 | 0.468 | 0.859 | ✗ |
| Q67 | What happens if the employee is declared bankrupt or insolve… | 0.360 | 0.886 | 0.500 | 0.500 | 0.583 | 0.446 | 0.898 | ✗ |
| Q68 | What happens if the employee is convicted of an offence invo… | 0.358 | 0.851 | 0.500 | 0.500 | 0.641 | 0.320 | 0.863 | ✗ |
| Q69 | What happens if the employee misappropriates Company money o… | 0.370 | 0.989 | 0.500 | 0.500 | 0.549 | 0.424 | 0.889 | ✗ |
| Q70 | What is stated about misconduct or insubordination by the em… | 0.336 | 0.870 | 0.500 | 0.500 | 0.555 | 0.503 | 0.891 | ✗ |
| Q71 | What happens if the employee infringes Company rules and reg… | 0.332 | 0.922 | 0.500 | 0.500 | 0.602 | 0.426 | 0.880 | ✗ |
| Q72 | What happens to losses caused by the employee during employm… | 0.320 | 0.999 | 0.500 | 0.500 | 0.577 | 0.502 | 0.885 | ✗ |
| Q73 | What are the employee guidelines described as? | 0.324 | 0.884 | 0.500 | 0.500 | 0.598 | 0.569 | 0.888 | ✗ |
| Q74 | How are the employee guidelines made available to employees? | 0.257 | 0.830 | 0.500 | 0.500 | 0.450 | 0.407 | 0.912 | ✗ |
| Q75 | Can the employee guidelines be changed? | 0.283 | 0.899 | 0.500 | 0.500 | 0.638 | 0.579 | 0.878 | ✗ |
| Q76 | What is the status of the employee guidelines under the agre… | 0.358 | 0.883 | 0.500 | 0.500 | 0.646 | 0.517 | 0.882 | ✗ |
| Q77 | Can the Employment Agreement be modified, amended, or termin… | 0.392 | 0.935 | 0.500 | 0.500 | 0.753 | 0.679 | 0.916 | ✗ |
| Q78 | How may the Employment Agreement be amended or cancelled? | 0.439 | 0.951 | 0.500 | 0.500 | 0.779 | 0.569 | 0.871 | ✗ |
| Q79 | What jurisdiction is specified in the agreement? | 0.453 | 0.854 | 0.500 | 0.500 | 0.596 | 0.315 | 0.845 | ✗ |
| Q80 | How are administrative disputes described as being handled? | 0.380 | 0.857 | 0.500 | 0.500 | 0.613 | 0.408 | 0.841 | ✗ |

---

## 7. RAG Triad Analysis

- **Average Context Relevance:** 0.3251
- **Average Faithfulness:** 0.5000
- **Average Answer Relevance:** 0.6142

> The low average context relevance suggests the retrieved chunks may not be closely matched to the questions. This is consistent with a possible retrieval-related issue, particularly if the document loaded in the vector store does not match the QA dataset.

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
