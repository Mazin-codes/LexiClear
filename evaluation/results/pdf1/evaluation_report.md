# LexiClear RAG Evaluation Report

**Generated:** 2026-09-24 20:09:56

> **Legal Domain Disclaimer:** This evaluation measures document-grounded retrieval quality, contextual relevance, response grounding, answer relevance, and similarity to expected document-derived answers. It does NOT measure legal validity, legal correctness in an authoritative sense, correctness of court interpretation, or professional legal advice quality.

---

## 1. Evaluation Setup

| Parameter | Value |
|-----------|-------|
| Evaluation timestamp | 2026-09-24 20:09:56 |
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
| Context Relevance (avg) | 0.4506 |
| Context Precision (avg NDCG) | 0.9862 |
| Context Recall (avg) | 0.5000 |
| Faithfulness (avg) | 0.5000 |
| Answer Relevance (avg) | 0.7587 |

### Existing Answer Quality Metrics

| Metric | New Run | Reference | Match? |
|--------|---------|-----------|--------|
| Semantic Similarity | 0.8108 | 0.5564 | ⚠ differs |
| BERTScore Precision | 0.8957 | 0.8736 | ⚠ differs |
| BERTScore Recall | 0.9393 | 0.8883 | ⚠ differs |
| BERTScore F1 | 0.9167 | 0.8807 | ⚠ differs |
| QA Accuracy | 0.7625 | 0.1600 | ⚠ differs |

#### Cross-check Note

Reference values are from `evaluation/metrics.txt` (25 questions, evaluated against the previously loaded document). If the current run differs materially, this is expected when `chroma_docs/` contains a different document than was present during the original run.

---

## 5. QA Accuracy Detail

- **Total questions:** 80
- **Correct:** 61
- **Incorrect:** 19
- **QA Accuracy:** 0.7625 (61/80)


---

## 6. Per-Question Results

| Q# | Question | CR | CP | CRec | Faith | AR | SemSim | BERT-F1 | QA |
|----|---- | --- | --- | --- | --- | --- | --- | --- | ----|
| Q1 | What position is the employee appointed to? | 0.455 | 0.984 | 0.500 | 0.500 | 0.715 | 0.946 | 0.960 | ✓ |
| Q2 | How long is the probationary period? | 0.400 | 0.981 | 0.500 | 0.500 | 0.837 | 0.962 | 0.948 | ✓ |
| Q3 | Can the company extend the probationary period? | 0.495 | 0.995 | 0.500 | 0.500 | 0.932 | 0.899 | 0.934 | ✓ |
| Q4 | Where is the employee initially stationed? | 0.308 | 1.000 | 0.500 | 0.500 | 0.752 | 0.966 | 0.955 | ✓ |
| Q5 | Can the company transfer the employee to another branch? | 0.345 | 1.000 | 0.500 | 0.500 | 0.739 | 0.954 | 0.945 | ✓ |
| Q6 | Can the employee be required to work outside the company's p… | 0.361 | 1.000 | 0.500 | 0.500 | 0.757 | 0.813 | 0.934 | ✓ |
| Q7 | Who can assign duties and responsibilities to the employee? | 0.494 | 0.992 | 0.500 | 0.500 | 0.735 | 0.928 | 0.897 | ✓ |
| Q8 | Must the employee follow company policies and applicable law… | 0.472 | 1.000 | 0.500 | 0.500 | 0.856 | 0.926 | 0.940 | ✓ |
| Q9 | Can the employee sign company documents without written cons… | 0.448 | 1.000 | 0.500 | 0.500 | 0.921 | 0.894 | 0.942 | ✓ |
| Q10 | Can the company modify its rules and regulations? | 0.391 | 0.999 | 0.500 | 0.500 | 0.760 | 0.775 | 0.881 | ✓ |
| Q11 | Where will arbitration proceedings be held? | 0.455 | 0.837 | 0.500 | 0.500 | 0.713 | 0.898 | 0.926 | ✓ |
| Q12 | Who is appointed as the sole arbitrator? | 0.460 | 0.842 | 0.500 | 0.500 | 0.712 | 0.886 | 0.930 | ✓ |
| Q13 | In which language will the arbitration proceedings be conduc… | 0.481 | 0.851 | 0.500 | 0.500 | 0.803 | 0.958 | 0.956 | ✓ |
| Q14 | What is the employee's annual CTC? | 0.335 | 0.994 | 0.500 | 0.500 | 0.716 | 0.907 | 0.913 | ✓ |
| Q15 | Can the employee disclose confidential company information? | 0.499 | 0.999 | 0.500 | 0.500 | 0.896 | 0.885 | 0.881 | ✓ |
| Q16 | Who owns intellectual property created by the employee durin… | 0.431 | 1.000 | 0.500 | 0.500 | 0.705 | 0.657 | 0.920 | ✗ |
| Q17 | What must the employee do with company documents after termi… | 0.504 | 1.000 | 0.500 | 0.500 | 0.753 | 0.807 | 0.911 | ✓ |
| Q18 | How long does the non-compete restriction apply after employ… | 0.400 | 1.000 | 0.500 | 0.500 | 0.753 | 0.555 | 0.871 | ✗ |
| Q19 | Can the employee directly or indirectly contact the company'… | 0.348 | 1.000 | 0.500 | 0.500 | 0.795 | 0.655 | 0.907 | ✗ |
| Q20 | What notice must the employee give to terminate the employme… | 0.542 | 1.000 | 0.500 | 0.500 | 0.823 | 0.751 | 0.909 | ✓ |
| Q21 | Can the employer terminate the employee immediately without … | 0.429 | 1.000 | 0.500 | 0.500 | 0.842 | 0.973 | 0.962 | ✓ |
| Q22 | What is the penalty for leaving the company before completin… | 0.440 | 1.000 | 0.500 | 0.500 | 0.782 | 0.767 | 0.888 | ✓ |
| Q23 | Can the company recover training expenses if the employee re… | 0.437 | 1.000 | 0.500 | 0.500 | 0.930 | 0.976 | 0.979 | ✓ |
| Q24 | Is severance pay provided if the employee is terminated for … | 0.468 | 0.999 | 0.500 | 0.500 | 0.868 | 0.944 | 0.949 | ✓ |
| Q25 | What law governs the employment agreement? | 0.541 | 0.999 | 0.500 | 0.500 | 0.661 | 0.932 | 0.958 | ✓ |
| Q26 | What is the date and place where the Employment Agreement is… | 0.479 | 1.000 | 0.500 | 0.500 | 0.687 | 0.923 | 0.922 | ✓ |
| Q27 | What is the registered office address of the Employer? | 0.317 | 0.999 | 0.500 | 0.500 | 0.692 | 0.962 | 0.917 | ✓ |
| Q28 | What is the name of the Employer? | 0.391 | 1.000 | 0.500 | 0.500 | 0.609 | 0.958 | 0.981 | ✓ |
| Q29 | What is the name of the Employee? | 0.414 | 1.000 | 0.500 | 0.500 | 0.644 | 0.963 | 0.917 | ✓ |
| Q30 | What is the Employee's residential address stated in the agr… | 0.436 | 0.998 | 0.500 | 0.500 | 0.727 | 0.849 | 0.895 | ✓ |
| Q31 | What may happen if the employee's work performance has not m… | 0.413 | 1.000 | 0.500 | 0.500 | 0.677 | 0.938 | 0.952 | ✓ |
| Q32 | What type of employee status may the employee receive after … | 0.449 | 1.000 | 0.500 | 0.500 | 0.681 | 0.788 | 0.921 | ✓ |
| Q33 | When does the employee become eligible for most company bene… | 0.350 | 1.000 | 0.500 | 0.500 | 0.696 | 0.884 | 0.909 | ✓ |
| Q34 | What standards is the employee expected to maintain after co… | 0.435 | 1.000 | 0.500 | 0.500 | 0.821 | 0.697 | 0.942 | ✗ |
| Q35 | Can the company transfer the employee to a future branch or … | 0.381 | 1.000 | 0.500 | 0.500 | 0.723 | 0.857 | 0.929 | ✓ |
| Q36 | What is the employee required to devote to the performance o… | 0.472 | 0.985 | 0.500 | 0.500 | 0.732 | 0.931 | 0.965 | ✓ |
| Q37 | Whose instructions must the employee follow in performing as… | 0.473 | 0.999 | 0.500 | 0.500 | 0.753 | 0.940 | 0.945 | ✓ |
| Q38 | What standard of conduct is required regarding the company's… | 0.467 | 1.000 | 0.500 | 0.500 | 0.477 | 0.460 | 0.858 | ✗ |
| Q39 | To whom does the employee directly report according to the a… | 0.522 | 1.000 | 0.500 | 0.500 | 0.721 | 0.870 | 0.941 | ✓ |
| Q40 | Can the employee engage in activities outside the scope of e… | 0.381 | 1.000 | 0.500 | 0.500 | 0.827 | 0.982 | 0.983 | ✓ |
| Q41 | What happens if the employee signs documents or commits on b… | 0.529 | 1.000 | 0.500 | 0.500 | 0.860 | 0.657 | 0.887 | ✗ |
| Q42 | Who is responsible for the employee's day-to-day management? | 0.413 | 0.993 | 0.500 | 0.500 | 0.745 | 0.915 | 0.948 | ✓ |
| Q43 | How are changes to the Company's rules and regulations made … | 0.425 | 0.999 | 0.500 | 0.500 | 0.680 | 0.891 | 0.885 | ✓ |
| Q44 | What happens if a claim, dispute, or difference arises conce… | 0.515 | 0.994 | 0.500 | 0.500 | 0.668 | 0.637 | 0.840 | ✗ |
| Q45 | Under which Act is the arbitration to be conducted? | 0.532 | 0.856 | 0.500 | 0.500 | 0.787 | 0.884 | 0.907 | ✓ |
| Q46 | What is the status of the arbitral award under the agreement… | 0.517 | 0.838 | 0.500 | 0.500 | 0.807 | 0.883 | 0.950 | ✓ |
| Q47 | What does the agreement state about salary if the employee f… | 0.440 | 1.000 | 0.500 | 0.500 | 0.862 | 0.945 | 0.972 | ✓ |
| Q48 | What types of company information are covered by the confide… | 0.484 | 0.994 | 0.500 | 0.500 | 0.837 | 0.944 | 0.895 | ✓ |
| Q49 | For what purpose may the employee use confidential company i… | 0.513 | 0.999 | 0.500 | 0.500 | 0.828 | 0.825 | 0.929 | ✓ |
| Q50 | What must the employee do to safeguard the Company's interes… | 0.467 | 1.000 | 0.500 | 0.500 | 0.696 | 0.633 | 0.860 | ✗ |
| Q51 | What happens to intellectual property created during the cou… | 0.394 | 1.000 | 0.500 | 0.500 | 0.557 | 0.665 | 0.871 | ✗ |
| Q52 | What does the agreement state about the Company's source cod… | 0.394 | 0.998 | 0.500 | 0.500 | 0.738 | 0.841 | 0.911 | ✓ |
| Q53 | What action may the Company take if the employee contravenes… | 0.412 | 1.000 | 0.500 | 0.500 | 0.691 | 0.770 | 0.920 | ✓ |
| Q54 | What items issued to the employee must be kept in safe custo… | 0.408 | 1.000 | 0.500 | 0.500 | 0.841 | 0.833 | 0.933 | ✓ |
| Q55 | When must the employee return company-issued items? | 0.423 | 1.000 | 0.500 | 0.500 | 0.812 | 0.838 | 0.912 | ✓ |
| Q56 | What may happen if the employee contravenes the non-compete … | 0.420 | 1.000 | 0.500 | 0.500 | 0.786 | 0.363 | 0.845 | ✗ |
| Q57 | How is the Company's client described in the client-restrict… | 0.462 | 0.994 | 0.500 | 0.500 | 0.904 | 0.762 | 0.903 | ✓ |
| Q58 | What consequence is stated for doing personal work or work f… | 0.412 | 1.000 | 0.500 | 0.500 | 0.591 | 0.512 | 0.905 | ✗ |
| Q59 | What does the Employment Agreement supersede regarding durat… | 0.516 | 1.000 | 0.500 | 0.500 | 0.869 | 0.893 | 0.941 | ✓ |
| Q60 | What happens to the employee's salary during the notice peri… | 0.505 | 1.000 | 0.500 | 0.500 | 0.646 | 0.754 | 0.915 | ✓ |
| Q61 | When is severance pay not provided under the agreement? | 0.462 | 0.999 | 0.500 | 0.500 | 0.763 | 0.917 | 0.931 | ✓ |
| Q62 | What happens if the employee commits an offence punishable u… | 0.558 | 1.000 | 0.500 | 0.500 | 0.888 | 0.640 | 0.888 | ✗ |
| Q63 | What recovery right does the Employer have if the employee c… | 0.410 | 1.000 | 0.500 | 0.500 | 0.764 | 0.789 | 0.944 | ✓ |
| Q64 | What training-related recovery right does the Company have? | 0.310 | 1.000 | 0.500 | 0.500 | 0.570 | 0.970 | 0.967 | ✓ |
| Q65 | What is one ground listed for termination involving dishones… | 0.466 | 0.995 | 0.500 | 0.500 | 0.812 | 0.856 | 0.912 | ✓ |
| Q66 | What happens if the employee commits a material breach of th… | 0.521 | 1.000 | 0.500 | 0.500 | 0.758 | 0.640 | 0.856 | ✗ |
| Q67 | What happens if the employee is declared bankrupt or insolve… | 0.484 | 0.996 | 0.500 | 0.500 | 0.824 | 0.689 | 0.925 | ✗ |
| Q68 | What happens if the employee is convicted of an offence invo… | 0.524 | 0.998 | 0.500 | 0.500 | 0.793 | 0.526 | 0.860 | ✗ |
| Q69 | What happens if the employee misappropriates Company money o… | 0.455 | 1.000 | 0.500 | 0.500 | 0.806 | 0.577 | 0.847 | ✗ |
| Q70 | What is stated about misconduct or insubordination by the em… | 0.530 | 1.000 | 0.500 | 0.500 | 0.745 | 0.764 | 0.907 | ✓ |
| Q71 | What happens if the employee infringes Company rules and reg… | 0.499 | 1.000 | 0.500 | 0.500 | 0.626 | 0.492 | 0.868 | ✗ |
| Q72 | What happens to losses caused by the employee during employm… | 0.447 | 1.000 | 0.500 | 0.500 | 0.699 | 0.701 | 0.872 | ✓ |
| Q73 | What are the employee guidelines described as? | 0.508 | 1.000 | 0.500 | 0.500 | 0.814 | 0.852 | 0.874 | ✓ |
| Q74 | How are the employee guidelines made available to employees? | 0.446 | 1.000 | 0.500 | 0.500 | 0.835 | 0.907 | 0.952 | ✓ |
| Q75 | Can the employee guidelines be changed? | 0.429 | 1.000 | 0.500 | 0.500 | 0.871 | 0.728 | 0.885 | ✓ |
| Q76 | What is the status of the employee guidelines under the agre… | 0.561 | 1.000 | 0.500 | 0.500 | 0.787 | 0.761 | 0.906 | ✓ |
| Q77 | Can the Employment Agreement be modified, amended, or termin… | 0.511 | 1.000 | 0.500 | 0.500 | 0.916 | 0.913 | 0.958 | ✓ |
| Q78 | How may the Employment Agreement be amended or cancelled? | 0.554 | 1.000 | 0.500 | 0.500 | 0.774 | 0.676 | 0.880 | ✗ |
| Q79 | What jurisdiction is specified in the agreement? | 0.498 | 0.911 | 0.500 | 0.500 | 0.573 | 0.920 | 0.956 | ✓ |
| Q80 | How are administrative disputes described as being handled? | 0.369 | 0.879 | 0.500 | 0.500 | 0.654 | 0.485 | 0.844 | ✗ |

---

## 7. RAG Triad Analysis

- **Average Context Relevance:** 0.4506
- **Average Faithfulness:** 0.5000
- **Average Answer Relevance:** 0.7587

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
