"""Mô-đun và công cụ tương tác: Đặt câu hỏi cho Agentic RAG
Tác giả: Lê Danh Giang (MSSV: 2A202603912 - Lớp L3B)

Hỗ trợ 2 mảng kiến thức:
1. Quy chế học vụ ĐHQGHN (Quy chế Đào tạo 2022 & Quy chế CTSV 2014 - 76 trang, 370 chunks)
2. Báo cáo thường niên Vinamilk 2025 (112 trang, 252 chunks gồm Bảng tài chính, Sơ đồ, Biểu đồ)

Cách dùng trong code Python:
    from ask import ask
    result = ask("Một tín chỉ tương đương bao nhiêu giờ lý thuyết?")
    print(result["answer"])

Cách dùng từ dòng lệnh (Terminal / PowerShell):
    python ask.py
    python ask.py "Doanh thu năm 2025 của Vinamilk là bao nhiêu?"
"""
import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent
sys.path.append(str(REPO_ROOT / "starter"))
sys.path.append(str(REPO_ROOT))

# Tự động nạp .env
env_candidates = [
    REPO_ROOT / ".env",
    REPO_ROOT.parent / ".env",
    Path("E:/AI_vin20k/K5-L3-Day06-DataIngestionEngineering-main/K5-L3-Day06-DataIngestionEngineering-main/starter/.env")
]
for p in env_candidates:
    if p.exists():
        load_dotenv(p)
        break

from starter.agentic import run_agent
from src.dense_retriever import DenseRetriever
from src.bm25_retriever import BM25Retriever
from src.hybrid_retriever import HybridRetriever
from src.gemini_controller import GeminiController

# Singleton cache lưu trữ pipeline để không phải nạp lại DB nhiều lần
_PIPELINE_CACHE = {}


def _get_pipeline(domain: str):
    if domain in _PIPELINE_CACHE:
        return _PIPELINE_CACHE[domain]

    if domain == "quiche":
        chunks_path = REPO_ROOT / "data" / "chunks.json"
        cache_db_path = REPO_ROOT / "data" / "gemini_embeddings_cache.sqlite"
        retriever = DenseRetriever(chunks_path=chunks_path, cache_db_path=cache_db_path)
        chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        chunks_dict = {c["id"]: c for c in chunks}
        controller = GeminiController(
            cache_db_path=REPO_ROOT / "data" / "llm_cache.sqlite"
        )
        config = {
            "retriever": retriever,
            "controller": controller,
            "chunks_dict": chunks_dict,
            "top_k": 5,
            "budget": 1500,
            "domain_name": "Quy chế Đào tạo & CTSV ĐHQGHN"
        }
    else:  # vinamilk
        chunks_path = REPO_ROOT / "data" / "advanced_chunks.json"
        cache_db_path = REPO_ROOT / "data" / "advanced_embeddings_cache.sqlite"
        chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        chunks_dict = {c["id"]: c for c in chunks}
        dense = DenseRetriever(chunks_path=chunks_path, cache_db_path=cache_db_path)
        bm25 = BM25Retriever(chunks_path=chunks_path)
        retriever = HybridRetriever(dense_retriever=dense, bm25_retriever=bm25, rrf_k=60)
        
        system_prompt = (
            "Bạn là trợ lý RAG chuyên gia phân tích Báo cáo thường niên Vinamilk 2025 (112 trang).\n"
            "Chỉ trả lời dựa trên context được cung cấp từ tài liệu Báo cáo thường niên Vinamilk 2025.\n"
            "Quy tắc tối quan trọng:\n"
            "1. Khi chưa có context tài liệu hoặc context hiện tại chưa đủ bằng chứng trả lời chính xác, hãy chọn action 'search'. Tạo search query ngắn gọn, tập trung vào thuật ngữ then chốt và số trang nếu có.\n"
            "2. Khi context đã có đủ bằng chứng, hãy chọn action 'answer':\n"
            "   - Trả lời chính xác, ghi rõ số liệu, đơn vị (triệu VND, %, v.v.), tên người, phòng ban.\n"
            "   - BẮT BUỘC chèn citation dạng [chunk_id] vào ngay sau câu/mệnh đề được trích xuất (ví dụ: [vnm_p109_250]).\n"
            "   - Liệt kê toàn bộ chunk_id hợp lệ vào danh sách citations.\n"
            "3. Nếu đã search nhiều lần mà tài liệu hoàn toàn không có thông tin (câu hỏi ngoại lai hoặc thiếu bằng chứng), BẮT BUỘC từ chối dứt khoát: 'Không đủ bằng chứng để trả lời.' với citations [].\n"
            "Định dạng JSON: {\"action\": \"search\", \"query\": \"...\"} hoặc {\"action\": \"answer\", \"answer\": \"...\", \"citations\": [...]}"
        )
        controller = GeminiController(
            cache_db_path=REPO_ROOT / "data" / "advanced_llm_cache.sqlite",
            system_prompt=system_prompt
        )
        config = {
            "retriever": retriever,
            "controller": controller,
            "chunks_dict": chunks_dict,
            "top_k": 5,
            "budget": 9000,
            "domain_name": "Báo cáo thường niên Vinamilk 2025 (112 trang)"
        }

    _PIPELINE_CACHE[domain] = config
    return config


def detect_domain(question: str) -> str:
    """Tự động phân loại câu hỏi thuộc Quy chế ĐHQGHN hay Vinamilk."""
    q_lower = question.lower()
    vnm_keywords = [
        "vinamilk", "vnm", "sữa", "doanh thu", "lợi nhuận", "cổ tức", "cổ phần",
        "hội đồng quản trị", "hđqt", "mai kiều liên", "nguyễn hạnh phúc",
        "báo cáo tài chính", "bctc", "tài sản", "nợ phải trả", "thù lao",
        "driftwood", "angkor", "nhà máy", "trang trại", "kiểm toán", "ubkt",
        "uỷ ban", "50 năm", "tổng giám đốc", "ban điều hành", "esg", "phát triển bền vững"
    ]
    for kw in vnm_keywords:
        if kw in q_lower:
            return "vinamilk"
    return "quiche"


def ask(question: str, domain: str = "auto", verbose: bool = True) -> dict:
    """Hàm đặt câu hỏi chính cho người dùng.
    
    Args:
        question: Chuỗi câu hỏi tiếng Việt.
        domain: 'auto' (tự phát hiện), 'quiche' (ĐHQGHN) hoặc 'vinamilk'.
        verbose: In ra console các bước thực thi chi tiết nếu True.
        
    Returns:
        dict: Chứa {
            'status': 'answered' | 'abstain',
            'answer': câu trả lời của AI,
            'citations': danh sách chunk IDs,
            'domain': tên mảng tài liệu đã chọn,
            'sources': danh sách thông tin chi tiết từng trích dẫn (trang, tài liệu, trích đoạn),
            'trace': các lượt search của agent
        }
    """
    if not question or not question.strip():
        return {
            "status": "error",
            "answer": "Vui lòng nhập câu hỏi hợp lệ (không được để trống).",
            "citations": [],
            "sources": []
        }

    actual_domain = detect_domain(question) if domain == "auto" else domain
    cfg = _get_pipeline(actual_domain)

    if verbose:
        print("\n" + "="*70)
        print(f"❓ CÂU HỎI: {question}")
        print(f"📚 TÀI LIỆU SỬ DỤNG: {cfg['domain_name']}")
        print("="*70)
        print("🤖 Agent đang suy nghĩ và truy xuất tài liệu...")

    trace = run_agent(
        question=question,
        controller=cfg["controller"],
        retriever=cfg["retriever"],
        top_k=cfg["top_k"],
        budget=cfg["budget"],
        max_searches=3
    )

    status = trace.get("status")
    answer = trace.get("answer", "")
    citations = trace.get("citations", [])
    events = trace.get("events", [])

    # Chuẩn bị thông tin nguồn chi tiết
    sources = []
    for cit in citations:
        chunk = cfg["chunks_dict"].get(cit, {})
        page = chunk.get("page", "N/A")
        source_name = chunk.get("source", "Tài liệu")
        snippet = chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
        sources.append({
            "chunk_id": cit,
            "page": page,
            "source": source_name,
            "snippet": snippet
        })

    if verbose:
        # In các bước tìm kiếm của agent
        search_count = 0
        for ev in events:
            if ev.get("event") == "search":
                search_count += 1
                q = ev.get("query")
                c_ids = ev.get("context_ids", [])
                print(f"  🔍 [Bước {search_count}] Tìm kiếm: '{q}' -> Tìm thấy {len(c_ids)} đoạn phù hợp {c_ids[:3]}")

        print("\n" + "-"*70)
        print("💡 CÂU TRẢ LỜI CỦA AGENT:")
        print(f"   {answer}")
        print("-"*70)

        if citations:
            print("📌 TRÍCH DẪN NGUỒN CỤ THỂ:")
            for s in sources:
                print(f"   • [{s['chunk_id']}] Trang {s['page']} ({s['source']}):")
                # Indent snippet
                snip_lines = s['snippet'].strip().split('\n')
                for sl in snip_lines[:3]:
                    print(f"     > {sl}")
        else:
            print("ℹ️ Không có trích dẫn (Câu trả lời từ chối do không có dữ liệu trong tài liệu).")
        print("="*70 + "\n")

    return {
        "status": status,
        "answer": answer,
        "citations": citations,
        "domain": cfg["domain_name"],
        "sources": sources,
        "trace": events
    }


def interactive_cli():
    """Giao diện dòng lệnh tương tác trực tiếp với người dùng."""
    print("="*70)
    print("🎓 CHÀO MỪNG BẠN ĐẾN VỚI HỆ THỐNG AGENTIC RAG — VINUNI AI20K")
    print("   Học viên: Lê Danh Giang (MSSV: 2A202603912 - Lớp L3B)")
    print("="*70)
    print("Hệ thống hỗ trợ 2 mảng tài liệu:")
    print("  [1] Quy chế ĐHQGHN (Đào tạo 2022 & CTSV 2014 — 76 trang)")
    print("  [2] Báo cáo thường niên Vinamilk 2025 (112 trang)")
    print("  [0] Tự động nhận diện theo nội dung câu hỏi (Mặc định)")
    print("  (Gõ 'exit' hoặc 'quit' bất cứ lúc nào để thoát)")
    print("="*70)

    mode = "auto"
    mode_choice = input("👉 Chọn chế độ [0/1/2] (Nhấn Enter để chọn Tự động): ").strip()
    if mode_choice == "1":
        mode = "quiche"
        print("✅ Đã chọn: Quy chế ĐHQGHN\n")
    elif mode_choice == "2":
        mode = "vinamilk"
        print("✅ Đã chọn: Báo cáo thường niên Vinamilk 2025\n")
    else:
        mode = "auto"
        print("✅ Đã chọn: Tự động nhận diện\n")

    while True:
        try:
            prompt_text = "❓ Nhập câu hỏi của bạn: "
            q = input(prompt_text).strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q", "thoat"]:
                print("Tạm biệt bạn! Cảm ơn bạn đã sử dụng hệ thống.")
                break
            if q.lower() in ["mode", "chedo", "doi"]:
                new_m = input("Chọn lại chế độ (0=Tự động, 1=Quy chế, 2=Vinamilk): ").strip()
                if new_m == "1":
                    mode = "quiche"
                elif new_m == "2":
                    mode = "vinamilk"
                else:
                    mode = "auto"
                print(f"✅ Đã đổi sang chế độ: {mode}\n")
                continue

            ask(q, domain=mode, verbose=True)
        except KeyboardInterrupt:
            print("\nĐã hủy truy vấn. Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Có lỗi xảy ra: {e}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        question_arg = " ".join(sys.argv[1:])
        ask(question_arg, domain="auto", verbose=True)
    else:
        interactive_cli()
