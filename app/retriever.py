import hashlib
import json
import os
import re
import uuid
import chromadb
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

from app.services.gemini_service import gemini_service

load_dotenv()

EMBED_MODEL = gemini_service.embed_model

def get_client():
    """Backward compatibility hook."""
    return gemini_service.get_client()

# Embedding caching directory and file path
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "embeddings.json")


def load_embedding_cache() -> dict[str, list[float]]:
    """Load cached embeddings from local JSON storage."""
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
    max_retries: int = 4,
    initial_delay: float = 2.0,
) -> list[list[float]]:
    """
    Call Gemini embed_content API via centralized GeminiService.
    """
    return gemini_service.embed_texts(texts, task_type=task, max_retries=max_retries)


def embed(texts: list[str], task: str) -> list[list[float]]:
    """
    Turn a list of texts into vector embeddings using the local cache first.
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
    """Tokenize text into lowercase alphanumeric words for BM25 keyword matching."""
    return [w for w in re.findall(r"\w+", text.lower()) if len(w) > 1]


class Retriever:
    """
    Hybrid retriever combining Gemini dense semantic vector search with BM25 sparse keyword search,
    merged via Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or uuid.uuid4().hex
        # Cosine distance collection in Chroma
        safe_col_name = f"iq-{re.sub(r'[^a-zA-Z0-9_-]', '', self.session_id)}"[:63]
        chroma_client = chromadb.Client()
        try:
            self.col = chroma_client.get_or_create_collection(
                safe_col_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            self.col = chroma_client.create_collection(
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
        if not self.chunks:
            return []
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
        """
        if not self.chunks:
            return []

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
        """
        if mode == "vector":
            return self.search_vector(query, k=k, source=source)
        if mode == "bm25":
            return self.search_bm25(query, k=k, source=source)
        return self.search_hybrid(query, k=k, source=source)

    def is_retrieval_weak(self, results: list[dict], min_sim: float = 0.35) -> bool:
        """
        Check if the retrieved results have insufficient relevance to the query.
        """
        if not results:
            return True

        top = results[0]
        if "score" in top and "distance" in top:
            return top["score"] < min_sim
        if "rrf_score" in top:
            return top["rrf_score"] < (1.0 / (60 + 15))
        return False
