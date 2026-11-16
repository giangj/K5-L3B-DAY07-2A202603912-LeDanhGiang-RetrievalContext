"""Hybrid Retriever combining Dense (Gemini embeddings) and BM25 using RRF."""
import logging
from pathlib import Path
from .dense_retriever import DenseRetriever
from .bm25_retriever import BM25Retriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(self, dense_retriever: DenseRetriever, bm25_retriever: BM25Retriever,
                 rrf_k: int = 60, candidate_k: int = 15):
        self.dense = dense_retriever
        self.bm25 = bm25_retriever
        self.rrf_k = rrf_k
        self.candidate_k = candidate_k
        logger.info("HybridRetriever initialized (rrf_k=%d, candidate_k=%d).", rrf_k, candidate_k)

    def search(self, query: str, *, filters: dict | None = None, top_k: int = 3) -> list[dict]:
        if not query.strip():
            return []
            
        dense_hits = self.dense.search(query, filters=filters, top_k=self.candidate_k)
        bm25_hits = self.bm25.search(query, filters=filters, top_k=self.candidate_k)
        
        rrf_scores = {}
        chunk_map = {}
        
        for rank, h in enumerate(dense_hits, start=1):
            cid = h["id"]
            chunk_map[cid] = h
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            
        for rank, h in enumerate(bm25_hits, start=1):
            cid = h["id"]
            if cid not in chunk_map:
                chunk_map[cid] = h
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            
        scored = []
        for cid, score in rrf_scores.items():
            item = dict(chunk_map[cid])
            item["score"] = score
            scored.append(item)
            
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    repo_root = Path(__file__).resolve().parents[1]
    dense = DenseRetriever(
        chunks_path=repo_root / "data" / "chunks.json",
        cache_db_path=repo_root / "data" / "gemini_embeddings_cache.sqlite"
    )
    bm25 = BM25Retriever(chunks_path=repo_root / "data" / "chunks.json")
    hybrid = HybridRetriever(dense, bm25)
    res = hybrid.search("Một tín chỉ bằng bao nhiêu giờ?", top_k=3)
    for r in res:
        print(f"[{r['id']}] score={r['score']:.4f} text={r['text'][:60]}")
