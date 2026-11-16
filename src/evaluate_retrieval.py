"""Evaluate and benchmark the 3 retrieval methods on dev and test sets."""
import json
import logging
import statistics
import time
from pathlib import Path
from dotenv import load_dotenv

from starter.baseline import pack_context, hit
from src.dense_retriever import DenseRetriever
from src.bm25_retriever import BM25Retriever
from src.hybrid_retriever import HybridRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def evaluate_method(name: str, retriever, questions: list[dict], split: str,
                    top_k: int = 3, budget: int = 800) -> tuple[dict, list[dict]]:
    split_questions = [q for q in questions if q.get("split") == split and q.get("answerable")]
    total = len(split_questions)
    if total == 0:
        return {}, []

    hit1_count = 0
    hit3_count = 0
    context_hit_count = 0
    durations_ms = []
    traces = []
    total_chars = 0

    for q in split_questions:
        qid = q["id"]
        q_text = q["question"]
        gold = q["gold"]
        filt = q.get("filter")

        start = time.perf_counter()
        results = retriever.search(q_text, filters=filt, top_k=top_k)
        dur = (time.perf_counter() - start) * 1000.0
        durations_ms.append(dur)

        is_hit1 = bool(results and hit(results[0], gold))
        is_hit3 = any(hit(r, gold) for r in results[:3])

        context, context_ids = pack_context(results, budget=budget)
        context_chunks = [r for r in results if r["id"] in context_ids]
        is_context_hit = any(hit(c, gold) for c in context_chunks)

        if is_hit1:
            hit1_count += 1
        if is_hit3:
            hit3_count += 1
        if is_context_hit:
            context_hit_count += 1

        total_chars += len(context)

        traces.append({
            "query_id": qid,
            "question": q_text,
            "filter": filt,
            "hit_at_1": is_hit1,
            "evidence_hit_at_3": is_hit3,
            "context_hit": is_context_hit,
            "retrieved_ids": [r["id"] for r in results],
            "context_ids": context_ids,
            "latency_ms": dur
        })

    summary = {
        "method": name,
        "split": split,
        "total_queries": total,
        "hit_at_1": hit1_count,
        "hit_at_1_rate": hit1_count / total,
        "evidence_hit_at_3": hit3_count,
        "evidence_hit_at_3_rate": hit3_count / total,
        "context_evidence_rate": context_hit_count / total,
        "context_evidence_count": context_hit_count,
        "avg_context_chars": total_chars / total,
        "median_latency_ms": statistics.median(durations_ms) if durations_ms else 0.0,
        "mean_latency_ms": statistics.mean(durations_ms) if durations_ms else 0.0,
        "cost_usd": 0.0  # Local cache / Free tier
    }

    return summary, traces


def run_all_retrieval_benchmarks():
    load_dotenv()
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    chunks_path = data_dir / "chunks.json"
    cache_path = data_dir / "gemini_embeddings_cache.sqlite"
    questions_path = data_dir / "questions.json"

    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    dense = DenseRetriever(chunks_path=chunks_path, cache_db_path=cache_path)
    bm25 = BM25Retriever(chunks_path=chunks_path)
    hybrid = HybridRetriever(dense_retriever=dense, bm25_retriever=bm25)

    methods = [
        ("BM25 (Lexical)", bm25),
        ("Dense (Gemini 768d)", dense),
        ("Hybrid (RRF Dense+BM25)", hybrid)
    ]

    results_dir = repo_root / "results" / "retrieval"
    results_dir.mkdir(parents=True, exist_ok=True)

    all_summaries = []

    for name, ret in methods:
        # Benchmark on Dev
        dev_summary, dev_traces = evaluate_method(name, ret, questions, split="dev")
        all_summaries.append(dev_summary)
        
        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("+", "_")
        dev_out = results_dir / f"{safe_name}_dev.json"
        dev_out.write_text(json.dumps({"summary": dev_summary, "traces": dev_traces}, ensure_ascii=False, indent=2), encoding="utf-8")
        
        logger.info(f"[{name} - DEV] Hit@1: {dev_summary['hit_at_1']}/{dev_summary['total_queries']} ({dev_summary['hit_at_1_rate']:.1%}) | "
                    f"Hit@3: {dev_summary['evidence_hit_at_3']}/{dev_summary['total_queries']} ({dev_summary['evidence_hit_at_3_rate']:.1%}) | "
                    f"Context Evidence: {dev_summary['context_evidence_count']}/{dev_summary['total_queries']} ({dev_summary['context_evidence_rate']:.1%}) | "
                    f"Latency: {dev_summary['median_latency_ms']:.2f}ms")

    # Save summary table
    summary_path = results_dir / "retrieval_comparison_dev.json"
    summary_path.write_text(json.dumps(all_summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved all retrieval dev benchmarks to %s", summary_path)


if __name__ == "__main__":
    run_all_retrieval_benchmarks()
