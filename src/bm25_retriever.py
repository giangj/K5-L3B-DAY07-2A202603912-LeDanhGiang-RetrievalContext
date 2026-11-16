"""BM25 Lexical Retriever with Vietnamese text tokenization."""
import json
import logging
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


class BM25Retriever:
    def __init__(self, chunks_path: Path, k1: float = 1.5, b: float = 0.75):
        self.chunks_path = Path(chunks_path)
        self.chunks = json.loads(self.chunks_path.read_text(encoding="utf-8"))
        self.k1 = k1
        self.b = b
        
        self.doc_lens = [len(tokenize(c["text"])) for c in self.chunks]
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 1.0
        self.doc_counts = [Counter(tokenize(c["text"])) for c in self.chunks]
        
        # Calculate DF and IDF
        self.df = Counter()
        for doc in self.doc_counts:
            for term in doc:
                self.df[term] += 1
                
        self.N = len(self.chunks)
        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1.0)
            
        logger.info("BM25Retriever initialized with %d chunks, vocab size %d.", self.N, len(self.idf))

    def search(self, query: str, *, filters: dict | None = None, top_k: int = 3) -> list[dict]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
            
        scored = []
        for idx, c in enumerate(self.chunks):
            if filters:
                meta = c.get("metadata", {})
                if any(meta.get(k) != v for k, v in filters.items()):
                    continue
                    
            doc_len = self.doc_lens[idx]
            counts = self.doc_counts[idx]
            score = 0.0
            for t in q_tokens:
                if t in counts:
                    f = counts[t]
                    idf = self.idf.get(t, 0.0)
                    denom = f + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                    score += idf * (f * (self.k1 + 1)) / denom
                    
            if score > 0:
                item = dict(c)
                item["score"] = score
                scored.append(item)
                
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    retriever = BM25Retriever(chunks_path=repo_root / "data" / "chunks.json")
    res = retriever.search("Một tín chỉ bằng bao nhiêu giờ?", top_k=3)
    for r in res:
        print(f"[{r['id']}] score={r['score']:.4f} text={r['text'][:60]}")
