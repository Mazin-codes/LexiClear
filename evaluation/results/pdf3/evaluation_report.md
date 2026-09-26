# LexiClear RAG Evaluation Report

**Generated:** 2026-09-25 21:42:00

> **Legal Domain Disclaimer:** This evaluation measures document-grounded retrieval quality, contextual relevance, response grounding, answer relevance, and similarity to expected document-derived answers. It does NOT measure legal validity, legal correctness in an authoritative sense, correctness of court interpretation, or professional legal advice quality.

---

## 1. Evaluation Setup

| Parameter | Value |
|-----------|-------|
| Evaluation timestamp | 2026-09-25 21:42:00 |
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
| Context Relevance (avg) | 0.3975 |
| Context Precision (avg NDCG) | 0.9681 |
| Context Recall (avg) | 0.5000 |
| Faithfulness (avg) | 0.5000 |
| Answer Relevance (avg) | 0.7028 |

### Existing Answer Quality Metrics

| Metric | New Run | Reference | Match? |
|--------|---------|-----------|--------|
| Semantic Similarity | 0.8021 | 0.5564 | ⚠ differs |
| BERTScore Precision | 0.8764 | 0.8736 | ✓ close |
| BERTScore Recall | 0.9422 | 0.8883 | ⚠ differs |
| BERTScore F1 | 0.9077 | 0.8807 | ⚠ differs |
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
| Q1 | What is the document called? | 0.301 | 0.849 | 0.500 | 0.500 | 0.573 | 0.914 | 0.932 | ✓ |
| Q2 | Where and on what date is the agreement made? | 0.437 | 0.916 | 0.500 | 0.500 | 0.654 | 0.917 | 0.933 | ✓ |
| Q3 | Who is the vendor under the agreement? | 0.427 | 0.996 | 0.500 | 0.500 | 0.696 | 0.932 | 0.888 | ✓ |
| Q4 | What is the vendor's father's name? | 0.296 | 0.996 | 0.500 | 0.500 | 0.637 | 0.405 | 0.862 | ✗ |
| Q5 | Where does the vendor reside? | 0.281 | 0.994 | 0.500 | 0.500 | 0.522 | 0.356 | 0.817 | ✗ |
| Q6 | Who is the purchaser under the agreement? | 0.511 | 1.000 | 0.500 | 0.500 | 0.503 | 0.764 | 0.823 | ✓ |
| Q7 | What is the purchaser's father's name? | 0.324 | 0.993 | 0.500 | 0.500 | 0.718 | 0.914 | 0.885 | ✓ |
| Q8 | Where does the purchaser reside? | 0.356 | 1.000 | 0.500 | 0.500 | 0.472 | 0.801 | 0.900 | ✓ |
| Q9 | How are the parties described in the agreement? | 0.421 | 0.887 | 0.500 | 0.500 | 0.347 | 0.679 | 0.798 | ✗ |
| Q10 | What does the vendor state about his ownership or entitlemen… | 0.459 | 1.000 | 0.500 | 0.500 | 0.718 | 0.905 | 0.948 | ✓ |
| Q11 | What has the vendor agreed to sell? | 0.358 | 0.999 | 0.500 | 0.500 | 0.516 | 0.667 | 0.886 | ✗ |
| Q12 | What property is the purchaser agreeing to buy? | 0.514 | 1.000 | 0.500 | 0.500 | 0.658 | 0.889 | 0.951 | ✓ |
| Q13 | What is the agreed sale price of the house? | 0.405 | 1.000 | 0.500 | 0.500 | 0.702 | 0.811 | 0.948 | ✓ |
| Q14 | What condition regarding encumbrances applies to the sale pr… | 0.399 | 0.997 | 0.500 | 0.500 | 0.806 | 0.709 | 0.930 | ✓ |
| Q15 | How much earnest money has the purchaser paid? | 0.461 | 1.000 | 0.500 | 0.500 | 0.732 | 0.968 | 0.956 | ✓ |
| Q16 | On what date was the earnest money paid? | 0.414 | 0.997 | 0.500 | 0.500 | 0.822 | 0.962 | 0.930 | ✓ |
| Q17 | What does the vendor acknowledge regarding the earnest money… | 0.495 | 0.997 | 0.500 | 0.500 | 0.773 | 0.755 | 0.851 | ✓ |
| Q18 | When is the balance amount of consideration to be paid? | 0.390 | 0.901 | 0.500 | 0.500 | 0.573 | 0.791 | 0.910 | ✓ |
| Q19 | Within what period must the sale be completed? | 0.465 | 1.000 | 0.500 | 0.500 | 0.849 | 0.942 | 0.897 | ✓ |
| Q20 | What does the agreement state about time in relation to the … | 0.403 | 0.961 | 0.500 | 0.500 | 0.645 | 0.604 | 0.916 | ✗ |
| Q21 | What must the vendor submit to the purchaser's advocate? | 0.474 | 0.987 | 0.500 | 0.500 | 0.641 | 0.982 | 0.967 | ✓ |
| Q22 | Within what time must the vendor submit the title deeds? | 0.511 | 1.000 | 0.500 | 0.500 | 0.885 | 0.924 | 0.954 | ✓ |
| Q23 | Why are the title deeds submitted to the purchaser's advocat… | 0.489 | 1.000 | 0.500 | 0.500 | 0.810 | 0.525 | 0.856 | ✗ |
| Q24 | What must the purchaser do after receiving the advocate's ti… | 0.466 | 0.992 | 0.500 | 0.500 | 0.759 | 0.592 | 0.878 | ✗ |
| Q25 | Within what period must the purchaser intimate the advocate'… | 0.427 | 0.971 | 0.500 | 0.500 | 0.706 | 0.949 | 0.935 | ✓ |
| Q26 | What happens if the purchaser's advocate reports that the ve… | 0.422 | 0.999 | 0.500 | 0.500 | 0.454 | 0.827 | 0.888 | ✓ |
| Q27 | Within what period must the vendor refund the earnest money … | 0.579 | 1.000 | 0.500 | 0.500 | 0.886 | 0.768 | 0.910 | ✓ |
| Q28 | Is interest payable on the earnest money when it is refunded… | 0.480 | 0.998 | 0.500 | 0.500 | 0.852 | 0.892 | 0.903 | ✓ |
| Q29 | What interest is payable if the vendor delays refunding the … | 0.515 | 0.999 | 0.500 | 0.500 | 0.807 | 0.664 | 0.893 | ✗ |
| Q30 | From when does the interest on delayed refund run? | 0.314 | 0.915 | 0.500 | 0.500 | 0.737 | 0.812 | 0.876 | ✓ |
| Q31 | What does the vendor declare about encumbrances? | 0.378 | 0.984 | 0.500 | 0.500 | 0.715 | 0.947 | 0.980 | ✓ |
| Q32 | When will vacant possession of the house be handed over? | 0.410 | 1.000 | 0.500 | 0.500 | 0.668 | 0.824 | 0.941 | ✓ |
| Q33 | What happens if the purchaser commits a breach of the agreem… | 0.483 | 0.997 | 0.500 | 0.500 | 0.715 | 0.884 | 0.923 | ✓ |
| Q34 | What additional right does the vendor have after purchaser b… | 0.446 | 1.000 | 0.500 | 0.500 | 0.624 | 0.547 | 0.900 | ✗ |
| Q35 | What happens if the vendor commits a breach of the agreement… | 0.424 | 0.985 | 0.500 | 0.500 | 0.631 | 0.836 | 0.894 | ✓ |
| Q36 | How much liquidated damages must the vendor pay for breach? | 0.382 | 0.984 | 0.500 | 0.500 | 0.685 | 0.628 | 0.918 | ✗ |
| Q37 | Does the vendor's breach provision include refund of earnest… | 0.418 | 0.990 | 0.500 | 0.500 | 0.941 | 0.890 | 0.944 | ✓ |
| Q38 | To whom will the vendor execute the conveyance deed? | 0.527 | 1.000 | 0.500 | 0.500 | 0.828 | 0.944 | 0.950 | ✓ |
| Q39 | When must the vendor execute the conveyance deed? | 0.548 | 1.000 | 0.500 | 0.500 | 0.767 | 0.897 | 0.942 | ✓ |
| Q40 | Can the purchaser nominate another person to receive the con… | 0.471 | 1.000 | 0.500 | 0.500 | 0.939 | 0.945 | 0.923 | ✓ |
| Q41 | Who must obtain the clearance certificate under section 230A… | 0.357 | 0.931 | 0.500 | 0.500 | 0.766 | 0.747 | 0.901 | ✓ |
| Q42 | Under which Act is the section 230A clearance certificate me… | 0.335 | 0.918 | 0.500 | 0.500 | 0.773 | 0.652 | 0.881 | ✗ |
| Q43 | Who bears the cost of obtaining the clearance certificate an… | 0.337 | 0.959 | 0.500 | 0.500 | 0.838 | 0.480 | 0.903 | ✗ |
| Q44 | What other permissions must the vendor obtain? | 0.353 | 0.981 | 0.500 | 0.500 | 0.645 | 0.751 | 0.893 | ✓ |
| Q45 | Who bears the expenses for preparation of the conveyance dee… | 0.513 | 0.998 | 0.500 | 0.500 | 0.790 | 0.922 | 0.925 | ✓ |
| Q46 | Who bears the cost of stamp charges? | 0.282 | 0.907 | 0.500 | 0.500 | 0.757 | 0.912 | 0.954 | ✓ |
| Q47 | Who bears the registration charges? | 0.278 | 0.954 | 0.500 | 0.500 | 0.671 | 0.679 | 0.909 | ✗ |
| Q48 | Who bears other out-of-pocket expenses under the agreement? | 0.359 | 0.891 | 0.500 | 0.500 | 0.748 | 0.822 | 0.936 | ✓ |
| Q49 | What is the property number stated in the Schedule? | 0.384 | 0.990 | 0.500 | 0.500 | 0.863 | 0.806 | 0.912 | ✓ |
| Q50 | Where is the scheduled property situated? | 0.352 | 1.000 | 0.500 | 0.500 | 0.662 | 0.906 | 0.912 | ✓ |
| Q51 | What type of property is described in the Schedule? | 0.348 | 0.974 | 0.500 | 0.500 | 0.485 | 0.661 | 0.855 | ✗ |
| Q52 | What is the approximate area of the scheduled property? | 0.275 | 0.997 | 0.500 | 0.500 | 0.797 | 0.818 | 0.892 | ✓ |
| Q53 | What rights are included with the scheduled property? | 0.403 | 0.998 | 0.500 | 0.500 | 0.739 | 0.735 | 0.935 | ✓ |
| Q54 | What is the northern boundary of the property? | 0.283 | 0.979 | 0.500 | 0.500 | 0.724 | 0.842 | 0.951 | ✓ |
| Q55 | What is the southern boundary of the property? | 0.280 | 0.974 | 0.500 | 0.500 | 0.752 | 0.859 | 0.935 | ✓ |
| Q56 | What is the eastern boundary of the property? | 0.292 | 0.977 | 0.500 | 0.500 | 0.806 | 0.917 | 0.963 | ✓ |
| Q57 | What is the western boundary of the property? | 0.291 | 0.983 | 0.500 | 0.500 | 0.698 | 0.880 | 0.920 | ✓ |
| Q58 | Does the Schedule identify the property by both number and l… | 0.277 | 0.966 | 0.500 | 0.500 | 0.588 | 0.865 | 0.869 | ✓ |
| Q59 | Does the Schedule specify the approximate size of the proper… | 0.277 | 0.959 | 0.500 | 0.500 | 0.553 | 0.716 | 0.903 | ✓ |
| Q60 | Does the property description include easements? | 0.275 | 1.000 | 0.500 | 0.500 | 0.800 | 0.882 | 0.933 | ✓ |
| Q61 | What is the stated northern boundary rather than the souther… | 0.154 | 0.793 | 0.500 | 0.500 | 0.619 | 0.746 | 0.926 | ✓ |
| Q62 | What is the stated eastern boundary rather than the western … | 0.149 | 0.754 | 0.500 | 0.500 | 0.596 | 0.717 | 0.901 | ✓ |
| Q63 | When do the parties sign the agreement according to the exec… | 0.469 | 0.885 | 0.500 | 0.500 | 0.592 | 0.935 | 0.926 | ✓ |
| Q64 | Who signs the agreement as vendor? | 0.464 | 0.980 | 0.500 | 0.500 | 0.722 | 0.911 | 0.905 | ✓ |
| Q65 | Who signs the agreement as purchaser? | 0.524 | 0.993 | 0.500 | 0.500 | 0.667 | 0.942 | 0.897 | ✓ |
| Q66 | Who is listed as the first witness? | 0.266 | 0.815 | 0.500 | 0.500 | 0.672 | 0.968 | 0.919 | ✓ |
| Q67 | Who is listed as the second witness? | 0.276 | 0.831 | 0.500 | 0.500 | 0.701 | 0.964 | 0.922 | ✓ |
| Q68 | What does the agreement require before the purchaser's advoc… | 0.511 | 0.995 | 0.500 | 0.500 | 0.846 | 0.775 | 0.886 | ✓ |
| Q69 | What two time periods are specified for title investigation … | 0.357 | 0.924 | 0.500 | 0.500 | 0.568 | 0.915 | 0.887 | ✓ |
| Q70 | What happens if the vendor does not repay the earnest money … | 0.537 | 0.999 | 0.500 | 0.500 | 0.732 | 0.836 | 0.900 | ✓ |
| Q71 | What event triggers payment of the balance sale consideratio… | 0.401 | 0.960 | 0.500 | 0.500 | 0.716 | 0.842 | 0.906 | ✓ |
| Q72 | What event is linked to handing over vacant possession? | 0.286 | 0.970 | 0.500 | 0.500 | 0.577 | 0.787 | 0.911 | ✓ |
| Q73 | What event is linked to execution of the conveyance deed by … | 0.485 | 1.000 | 0.500 | 0.500 | 0.779 | 0.688 | 0.911 | ✗ |
| Q74 | What consequence follows purchaser breach apart from forfeit… | 0.502 | 0.995 | 0.500 | 0.500 | 0.765 | 0.714 | 0.926 | ✓ |
| Q75 | What monetary consequence follows vendor breach? | 0.430 | 0.982 | 0.500 | 0.500 | 0.580 | 0.844 | 0.867 | ✓ |
| Q76 | Which party bears conveyance deed, stamp, registration, and … | 0.345 | 0.958 | 0.500 | 0.500 | 0.596 | 0.637 | 0.882 | ✗ |
| Q77 | Which party is responsible for obtaining permissions require… | 0.451 | 1.000 | 0.500 | 0.500 | 0.632 | 0.735 | 0.917 | ✓ |
| Q78 | What does the agreement say about the house being free from … | 0.497 | 1.000 | 0.500 | 0.500 | 0.874 | 0.872 | 0.886 | ✓ |
| Q79 | What is the relationship between the earnest money and the b… | 0.464 | 0.994 | 0.500 | 0.500 | 0.867 | 0.762 | 0.875 | ✓ |
| Q80 | What is the difference between the sale price and the earnes… | 0.402 | 1.000 | 0.500 | 0.500 | 0.700 | 0.765 | 0.849 | ✓ |

---

## 7. RAG Triad Analysis

- **Average Context Relevance:** 0.3975
- **Average Faithfulness:** 0.5000
- **Average Answer Relevance:** 0.7028

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
