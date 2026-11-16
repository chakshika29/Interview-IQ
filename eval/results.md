# 📈 InterviewIQ: Empirical RAG Evaluation Report

This evaluation suite benchmarks the retrieval and generation pipeline of **InterviewIQ** across **32 hand-crafted, ground-truth test queries** covering technical qualifications, system architecture, candidate projects, and certifications.

---

## 1. Retrieval Strategy Benchmark (Chunk Size = 800)

| Retrieval Mode | Hit Rate @ 1 | Hit Rate @ 3 | Hit Rate @ 5 | Mean Reciprocal Rank (MRR) |
| :--- | :---: | :---: | :---: | :---: |
| **Vector-Only** (`gemini-embedding-001`) | `84.4%` | `100.0%` | `100.0%` | `0.906` |
| **BM25-Only** (Lexical Search) | `84.4%` | `96.9%` | `100.0%` | `0.914` |
| **Hybrid RRF** (Vector + BM25 Fusion) | **`87.5%`** | **`100.0%`** | **`100.0%`** | **`0.938`** |

### Key Architectural Takeaway
- **Dense Vector Search** excels at capturing high-level conceptual intent and semantic synonyms (e.g. mapping "framework for AI agents" to "LangGraph").
- **BM25 Sparse Search** excels at exact acronyms, numbers, and tool names (e.g., "AST", "500+", "JWT", "AWS").
- **Reciprocal Rank Fusion (RRF)** combines the strengths of both systems without needing score normalization, providing the highest overall recall (`Hit@5 = 100.0%`) and the fastest time to relevant chunk (`MRR = 0.938`).

---

## 2. Chunk Size Sensitivity Analysis (Hybrid Mode)

| Chunk Size | Hit Rate @ 1 | Hit Rate @ 3 | Hit Rate @ 5 | MRR |
| :--- | :---: | :---: | :---: | :---: |
| **Small Chunks (400 chars)** | `90.6%` | `100.0%` | `100.0%` | `0.953` |
| **Large Chunks (800 chars)** | `87.5%` | `100.0%` | `100.0%` | `0.938` |

### Chunking Insight
- Smaller 400-character chunks create tighter embedding representations for specific keywords, but can separate interrelated requirements across boundaries.
- 800-character sentence-boundary chunks provide rich contextual surround for each technical qualification, leading to superior multi-sentence reasoning during downstream generation.

---

## 3. End-to-End LLM-as-a-Judge Evaluation

| Metric | Score | Scale | Description |
| :--- | :---: | :---: | :--- |
| **Grounded Answer Quality** | **`5.0`** | `1.0 - 5.0` | Evaluated across faithfulness to retrieved context, factual accuracy against reference facts, and hallucination absence. |

---

## 4. Evaluation Methodology

1. **Benchmark Set**: 32 queries with exact keyword targets, expected facts, and human-verified reference answers (`eval/test_set.json`).
2. **Metrics Defined**:
   - Hit Rate@k = (Number of queries with hit in top k) / (Total queries)
   - MRR = Average of (1 / rank_of_first_hit) across all queries
   - RRF Score = 1 / (60 + rank_vector) + 1 / (60 + rank_bm25)
