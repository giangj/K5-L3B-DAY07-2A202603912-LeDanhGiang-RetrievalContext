"""Dense Retriever using Gemini Embeddings (768d) and SQLite cache from Day 6."""
import hashlib
import json
import logging
import math
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class DenseRetriever:
    def __init__(self, chunks_path: Path, cache_db_path: Path, api_key: str | None = None,
                 model_name: str = "models/gemini-embedding-001", dimensions: int = 768):
        self.chunks_path = Path(chunks_path)
        self.cache_db_path = Path(cache_db_path)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.dimensions = dimensions
        
        self.chunks = json.loads(self.chunks_path.read_text(encoding="utf-8"))
        self.conn = sqlite3.connect(self.cache_db_path)
        self._init_db()
        self._load_chunk_embeddings()
        logger.info("DenseRetriever ready with %d chunks and %d indexed vectors.", len(self.chunks), len(self.chunk_vectors))

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                text_hash TEXT PRIMARY KEY,
                vector_json TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def _load_chunk_embeddings(self):
        self.chunk_vectors = {}
        missing = []
        cur = self.conn.cursor()
        for c in self.chunks:
            h = hashlib.sha256(c["text"].encode("utf-8")).hexdigest()
            cur.execute("SELECT vector_json FROM cache WHERE text_hash=?", (h,))
            row = cur.fetchone()
            if row:
                self.chunk_vectors[c["id"]] = json.loads(row[0])
            else:
                missing.append((c, h))

        if missing:
            logger.warning("Missing embeddings for %d chunks, embedding via API...", len(missing))
            for c, h in missing:
                vec = self._embed_api(c["text"])
                cur.execute("INSERT OR REPLACE INTO cache (text_hash, vector_json) VALUES (?, ?)", (h, json.dumps(vec)))
                self.chunk_vectors[c["id"]] = vec
            self.conn.commit()

    def _embed_api(self, text: str) -> list[float]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required for embedding API call")
        url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:embedContent?key={self.api_key}"
        payload = json.dumps({
            "model": self.model_name,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.dimensions
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("embedding", {}).get("values", [])
            except Exception as e:
                logger.warning("Embedding API error (attempt %d/4): %s", attempt + 1, e)
                time.sleep(2 ** attempt)
        raise RuntimeError("Failed to embed text after 4 retries")

    def embed_query(self, query: str) -> list[float]:
        h = hashlib.sha256(query.encode("utf-8")).hexdigest()
        cur = self.conn.cursor()
        cur.execute("SELECT vector_json FROM cache WHERE text_hash=?", (h,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        vec = self._embed_api(query)
        cur.execute("INSERT OR REPLACE INTO cache (text_hash, vector_json) VALUES (?, ?)", (h, json.dumps(vec)))
        self.conn.commit()
        return vec

    def search(self, query: str, *, filters: dict | None = None, top_k: int = 3) -> list[dict]:
        if not query.strip():
            return []
        q_vec = self.embed_query(query)
        scored = []
        for c in self.chunks:
            # Check filter if provided
            if filters:
                match = True
                meta = c.get("metadata", {})
                for k, v in filters.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            cid = c["id"]
            if cid in self.chunk_vectors:
                sim = cosine_similarity(q_vec, self.chunk_vectors[cid])
                item = dict(c)
                item["score"] = sim
                scored.append(item)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


if __name__ == "__main__":
    load_dotenv()
    repo_root = Path(__file__).resolve().parents[1]
    retriever = DenseRetriever(
        chunks_path=repo_root / "data" / "chunks.json",
        cache_db_path=repo_root / "data" / "gemini_embeddings_cache.sqlite"
    )
    res = retriever.search("Một tín chỉ bằng bao nhiêu giờ?", top_k=3)
    for r in res:
        print(f"[{r['id']}] score={r['score']:.4f} text={r['text'][:60]}")
