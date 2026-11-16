"""Gemini LLM Controller with automatic multi-model fallback and local disk caching."""
import hashlib
import json
import logging
import os
import sqlite3
import time
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý học vụ thông minh tại ĐHQGHN, thực hiện truy xuất bằng chứng và trả lời câu hỏi quy chế.
Bạn có công cụ tìm kiếm trong cơ sở dữ liệu quy chế (gồm Quy chế Đào tạo 2022 và Quy chế Công tác sinh viên 2014).

Quy tắc làm việc:
1. Khi chưa có context tài liệu hoặc context hiện tại chưa đủ bằng chứng trả lời chính xác, hãy chọn action 'search'. Tạo search query ngắn gọn, tập trung vào thuật ngữ then chốt.
2. Khi context đã có đủ bằng chứng, hãy chọn action 'answer':
   - Câu trả lời PHẢI dựa trực tiếp trên context được cung cấp.
   - BẮT BUỘC chèn citation dạng [chunk_id] vào ngay sau mệnh đề được trích xuất.
   - Liệt kê toàn bộ chunk_id hợp lệ vào danh sách citations.
   - Ví dụ: {"action": "answer", "answer": "Một tín chỉ tương đương 15 giờ tín chỉ lý thuyết [quiche_daotao_2022_p3_para1].", "citations": ["quiche_daotao_2022_p3_para1"]}
3. NẾU ĐÃ TÌM KIẾM MÀ CONTEXT HOÀN TOÀN KHÔNG CÓ BẰNG CHỨNG (câu hỏi nằm ngoài phạm vi quy chế, hoặc không đủ thông tin), BẮT BUỘC từ chối dứt khoát:
   {"action": "answer", "answer": "Không đủ bằng chứng để trả lời.", "citations": []}

Định dạng JSON output:
{"action": "search", "query": "..."}
HOẶC
{"action": "answer", "answer": "...", "citations": ["chunk-id"]}
"""


class GeminiController:
    def __init__(self, api_key: str | None = None,
                 models: list[str] | None = None,
                 cache_db_path: Path | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiController")
        self.models = models or [
            "models/gemini-3.1-flash-lite-preview",
            "models/gemini-3.5-flash",
            "models/gemini-3-flash-preview"
        ]
        self.cache_db_path = cache_db_path
        self.conn = None
        if self.cache_db_path:
            self.conn = sqlite3.connect(str(self.cache_db_path))
            self._init_cache()

    def _init_cache(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS llm_cache (
                prompt_hash TEXT PRIMARY KEY,
                response_json TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def _get_cache(self, key: str) -> dict | None:
        if not self.conn:
            return None
        cur = self.conn.cursor()
        cur.execute("SELECT response_json FROM llm_cache WHERE prompt_hash=?", (key,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def _set_cache(self, key: str, val: dict):
        if not self.conn:
            return
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO llm_cache (prompt_hash, response_json) VALUES (?, ?)", (key, json.dumps(val)))
        self.conn.commit()

    def decide(self, question: str, history: list[dict]) -> dict:
        user_msg = f"Câu hỏi của người dùng: {question}\n\n"
        if not history:
            user_msg += "Hiện tại chưa có lượt tìm kiếm nào. Hãy thực hiện tìm kiếm đầu tiên."
        else:
            latest = history[-1]
            queries = latest.get("queries", [])
            context = latest.get("context", "")
            context_ids = latest.get("context_ids", [])
            user_msg += f"Lịch sử các query đã tìm: {queries}\n"
            user_msg += f"Danh sách chunk IDs có trong context hiện tại: {context_ids}\n\n"
            user_msg += f"--- NỘI DUNG TÀI LIỆU TRÍCH XUẤT ĐƯỢC (CONTEXT) ---\n{context}\n------------------------------------------------\n\n"
            user_msg += "Đọc kỹ context trên. Nếu đủ bằng chứng trả lời, hãy trả lời kèm citation [chunk_id]. Nếu sau các lượt tìm kiếm mà tài liệu không có thông tin này, hãy từ chối: 'Không đủ bằng chứng để trả lời.' với citations []. Nếu cần tìm thêm, hãy đưa query tiếp theo."

        prompt_full = f"{SYSTEM_PROMPT}\n\n{user_msg}"
        cache_key = hashlib.sha256(prompt_full.encode("utf-8")).hexdigest()

        cached_resp = self._get_cache(cache_key)
        if cached_resp:
            return cached_resp

        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt_full}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }).encode("utf-8")

        for model_name in self.models:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={self.api_key}"
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            for attempt in range(2):
                try:
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        parsed = json.loads(text)
                        if "action" not in parsed:
                            if "query" in parsed:
                                parsed["action"] = "search"
                            elif "answer" in parsed:
                                parsed["action"] = "answer"
                        if parsed.get("action") == "answer" and "citations" not in parsed:
                            parsed["citations"] = []
                        self._set_cache(cache_key, parsed)
                        return parsed
                except urllib.error.HTTPError as e:
                    logger.warning("Model %s HTTP error %d (attempt %d/2)", model_name, e.code, attempt + 1)
                    if e.code in (404, 429, 503):
                        break  # Fallback to next model
                    time.sleep(1)
                except Exception as e:
                    logger.warning("Model %s error %s (attempt %d/2)", model_name, e, attempt + 1)
                    time.sleep(1)

        # Fallback if all models fail
        return {"action": "answer", "answer": "Không đủ bằng chứng để trả lời.", "citations": []}


if __name__ == "__main__":
    load_dotenv()
    repo_root = Path(__file__).resolve().parents[1]
    ctrl = GeminiController(cache_db_path=repo_root / "data" / "llm_cache.sqlite")
    res = ctrl.decide("Một tín chỉ bằng bao nhiêu giờ?", [])
    print("Initial decision:", res)
