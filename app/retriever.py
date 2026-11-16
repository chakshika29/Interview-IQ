import hashlib
import json
import os
import random
import re
import time
import uuid
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from rank_bm25 import BM25Okapi

# WHY: Load environment variables so we can access GEMINI_API_KEY
load_dotenv()

EMBED_MODEL = "gemini-embedding-001"


def get_client() -> genai.Client:
    """
    Get or initialize the Google GenAI client from environment or Streamlit secrets.

    WHY: In cloud deployments (Streamlit Cloud, Render, Railway, Hugging Face Spaces),
    API keys are provided via cloud secrets or container environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
        except Exception:
            pass
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Please set it in .env, environment, or Streamlit secrets.")
    return genai.Client(api_key=api_key)

# WHY: Embedding caching directory and file path
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "embeddings.json")


def load_embedding_cache() -> dict[str, list[float]]:
    """
    Load cached embeddings from local JSON storage.

    WHY: Free Gemini API tier has strict requests-per-minute limits. Caching embeddings
    locally avoids re-embedding unchanged documents every time the app or tests run.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_embedding_cache(cache: dict[str, list[float]]) -> None:
    """Save the updated embedding cache to disk."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass


def get_cache_key(text: str, task: str) -> str:
    """Compute a deterministic hash for a given text and task type."""
    return hashlib.sha256(f"{task}:{text}".encode("utf-8")).hexdigest()


def embed_batch_with_retry(
    texts: list[str],
    task: str,
    max_retries: int = 5,
    initial_delay: float = 2.0,
) -> list[list[float]]:
    """
    Call Gemini embed_content API with exponential backoff on HTTP 429 rate limits.

    WHY: Embedding multiple chunks rapidly can trigger rate limit (429) errors.
    Exponential backoff ensures transient errors are retried automatically.
    """
    delay = initial_delay
    last_err = None

    for attempt in range(max_retries):
        try:
            client_instance = get_client()
            resp = client_instance.models.embed_content(
                model=EMBED_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task),
            )
            return [e.values for e in resp.embeddings]
        except (errors.ClientError, errors.ServerError, Exception) as exc:
            last_err = exc
            err_msg = str(exc)
            is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
            is_unavailable = "503" in err_msg or "UNAVAILABLE" in err_msg

            if (is_rate_limit or is_unavailable) and attempt < max_retries - 1:
                sleep_time = delay + random.uniform(0.5, 1.5)
                time.sleep(sleep_time)
                delay *= 2
                continue
            raise last_err

    raise RuntimeError(f"Embedding failed after {max_retries} attempts: {last_err}")


def embed(texts: list[str], task: str) -> list[list[float]]:
    """
    Turn a list of texts into vector embeddings using the cache first.

    WHY: Checks the local cache before making API calls. Only missing texts
    are sent to the Gemini API, saving quota and accelerating execution.
    """
    if not texts:
        return []

    cache = load_embedding_cache()
    vectors = [None] * len(texts)
    missing_indices = []
    missing_texts = []

    for i, t in enumerate(texts):
        key = get_cache_key(t, task)
        if key in cache:
            vectors[i] = cache[key]
        else:
            missing_indices.append(i)
            missing_texts.append(t)

    # If any texts were not cached, embed them in batches of 50
    if missing_texts:
        new_embeddings = []
        for i in range(0, len(missing_texts), 50):
            batch = missing_texts[i : i + 50]
            emb_batch = embed_batch_with_retry(batch, task)
            new_embeddings.extend(emb_batch)

        for idx, text, emb in zip(missing_indices, missing_texts, new_embeddings):
            vectors[idx] = emb
            cache[get_cache_key(text, task)] = emb

        save_embedding_cache(cache)

    return vectors


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase alphanumeric words for BM25 keyword matching.

    WHY: BM25 computes term frequencies over discrete word tokens rather than vectors.
    """
    return [w for w in re.findall(r"\w+", text.lower()) if len(w) > 1]


class Retriever:
    """
    Hybrid retriever combining Gemini dense semantic vector search with BM25 sparse keyword search,
    merged via Reciprocal Rank Fusion (RRF).

    WHY: Dense vector search excels at high-level semantic meaning and paraphrasing,
    while BM25 keyword search excels at exact acronyms, specific library names (e.g. LangGraph),
    and precise technical terms. Hybrid RRF merges both strengths without requiring a heavy
    GPU cross-encoder model.
    """

    def __init__(self):
        # Cosine distance collection in Chroma
        self.col = chromadb.Client().create_collection(
            f"iq-{uuid.uuid4().hex}",
            metadata={"hnsw:space": "cosine"},
        )
        self.chunks: list[dict] = []
        self.bm25: BM25Okapi | None = None
        self.tokenized_corpus: list[list[str]] = []

    def add(self, chunks):
        """Add document chunks to both the vector database and BM25 index."""
        if not chunks:
            return

        texts = [c.text for c in chunks]
        ids = [c.id for c in chunks]
        metadatas = [{"source": c.source, "page": c.page or 0} for c in chunks]

        # Add to ChromaDB vector store
        self.col.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embed(texts, "RETRIEVAL_DOCUMENT"),
        )

        # Append to BM25 in-memory index
        for c in chunks:
            self.chunks.append({
                "id": c.id,
                "text": c.text,
                "source": c.source,
                "page": c.page or 0,
            })
            self.tokenized_corpus.append(tokenize(c.text))

        # Re-initialize BM25 with all tokenized documents
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search_vector(self, query: str, k: int = 4, source: str | None = None) -> list[dict]:
        """Dense semantic vector similarity search via ChromaDB."""
        where = {"source": source} if source else None
        res = self.col.query(
            query_embeddings=embed([query], "RETRIEVAL_QUERY"),
            n_results=min(k, len(self.chunks)),
            where=where,
        )

        results = []
        if res["documents"] and len(res["documents"][0]) > 0:
            for d, m, doc_id, dist in zip(
                res["documents"][0],
                res["metadatas"][0],
                res["ids"][0],
                res["distances"][0],
            ):
                similarity = 1.0 - dist  # Cosine similarity
                results.append({
                    "id": doc_id,
                    "text": d,
                    "source": m["source"],
                    "page": m["page"],
                    "score": round(similarity, 4),
                    "distance": round(dist, 4),
                })
        return results

    def search_bm25(self, query: str, k: int = 4, source: str | None = None) -> list[dict]:
        """Sparse keyword search via BM25."""
        if not self.bm25 or not self.chunks:
            return []

        tokens = tokenize(query)
        scores = self.bm25.get_scores(tokens)

        # Filter and rank candidates
        scored_docs = []
        for doc, score in zip(self.chunks, scores):
            if source and doc["source"] != source:
                continue
            scored_docs.append({
                "id": doc["id"],
                "text": doc["text"],
                "source": doc["source"],
                "page": doc["page"],
                "score": round(float(score), 4),
            })

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:k]

    def search_hybrid(
        self,
        query: str,
        k: int = 4,
        source: str | None = None,
        rrf_k: int = 60,
    ) -> list[dict]:
        """
        Merge vector and BM25 search rankings using Reciprocal Rank Fusion (RRF).

        WHY: RRF combines the rank positions from multiple distinct retrieval algorithms:
        RRF_Score = 1 / (60 + rank_vector) + 1 / (60 + rank_bm25).
        It does not require normalising different score distributions (e.g. cosine vs BM25),
        and gives top priority to documents favored by both search strategies.
        """
        pool_size = max(20, k * 3)

        vector_results = self.search_vector(query, k=pool_size, source=source)
        bm25_results = self.search_bm25(query, k=pool_size, source=source)

        rrf_scores: dict[str, float] = {}
        doc_map: dict[str, dict] = {}

        for rank, item in enumerate(vector_results, start=1):
            doc_id = item["id"]
            doc_map[doc_id] = item
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))

        for rank, item in enumerate(bm25_results, start=1):
            doc_id = item["id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = item
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))

        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids[:k]:
            item = dict(doc_map[doc_id])
            item["rrf_score"] = round(rrf_scores[doc_id], 5)
            results.append(item)

        return results

    def search(self, query: str, k: int = 4, source: str | None = None, mode: str = "hybrid") -> list[dict]:
        """
        Primary search interface supporting 'hybrid', 'vector', and 'bm25' retrieval modes.

        WHY: Defaulting to hybrid provides the strongest retrieval quality, while supporting
        'vector' and 'bm25' modes enables head-to-head empirical benchmarking in Phase 4.
        """
        if mode == "vector":
            return self.search_vector(query, k=k, source=source)
        if mode == "bm25":
            return self.search_bm25(query, k=k, source=source)
        return self.search_hybrid(query, k=k, source=source)

    def is_retrieval_weak(self, results: list[dict], min_sim: float = 0.35) -> bool:
        """
        Check if the retrieved results have insufficient relevance to the query.

        WHY: Guardrail mechanism. If the documents don't contain relevant facts,
        recognizing weak retrieval prevents the model from hallucinating false answers.
        """
        if not results:
            return True

        # If vector distance or similarity is available, check top result
        top = results[0]
        if "score" in top and "distance" in top:
            # For vector mode, score is similarity
            return top["score"] < min_sim
        if "rrf_score" in top:
            # If RRF score is tiny (only low ranks in one list)
            return top["rrf_score"] < (1.0 / (60 + 15))
        return False
