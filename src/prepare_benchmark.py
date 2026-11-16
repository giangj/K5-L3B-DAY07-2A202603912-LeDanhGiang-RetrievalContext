"""Format Day 6 questions and add unanswerable cases into Day 7 benchmark.
Aligns gold evidence quotes with exact chunk substring to satisfy baseline.py validate().
"""
import json
import re
from pathlib import Path


def prepare_benchmark():
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    chunks_path = data_dir / "chunks.json"
    day6_q_path = Path("E:/AI_vin20k/K5-L3-Day06-DataIngestionEngineering-main/K5-L3-Day06-DataIngestionEngineering-main/starter/data/benchmark_questions.json")
    
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    day6_questions = json.loads(day6_q_path.read_text(encoding="utf-8"))
    
    formatted_questions = []
    agent_cases = []
    
    # Helper to find exact substring in chunk
    def align_evidence(gold_source, gold_page, quote, q_id):
        if q_id == "q10":
            quote = "Sinh viên bị cảnh cáo khi thi học phần nào sẽ bị trừ 50% số điểm đạt được"
        words = re.sub(r"\s+", " ", quote.strip()).split()
        pattern = r"\s+".join(re.escape(w) for w in words)
        cands = [c for c in chunks if c["source_id"] == gold_source and c["page"] == gold_page]
        for c in cands:
            m = re.search(pattern, c["text"])
            if m:
                return m.group(0)
        raise ValueError(f"Could not align evidence for {q_id} on {gold_source} page {gold_page}")

    # 1. Format existing 22 answerable questions
    for q in day6_questions:
        q_id = q["id"]
        split = q["split"]
        question_text = q["question"]
        expected_ans = q["expected_answer"]
        gold_source = q["gold_source_id"]
        gold_page = q["gold_page"]
        raw_evidence = q["evidence_quote"]
        exact_evidence = align_evidence(gold_source, gold_page, raw_evidence, q_id)
        filt = q.get("filter")
        
        item = {
            "id": q_id,
            "split": split,
            "type": q.get("type", "direct"),
            "question": question_text,
            "expected_answer": expected_ans,
            "answerable": True,
            "expected_behavior": "search_and_answer",
            "gold": [
                {
                    "source_id": gold_source,
                    "page": gold_page,
                    "evidence": exact_evidence
                }
            ]
        }
        if filt:
            item["filter"] = filt
            
        formatted_questions.append(item)
        
        agent_cases.append({
            "id": q_id,
            "split": split,
            "question": question_text,
            "answerable": True,
            "expected_behavior": "search_and_answer"
        })
        
    # 2. Add 4 unanswerable questions (2 Dev, 2 Test)
    unanswerable = [
        {
            "id": "q_dev_unans_01",
            "split": "dev",
            "question": "Mức học bổng khuyến khích học tập bằng tiền mặt cụ thể của năm học 2024-2025 tại ĐHQGHN là bao nhiêu triệu đồng mỗi tháng?",
            "expected_answer": "Không đủ bằng chứng để trả lời.",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Quy chế chỉ quy định nguyên tắc xét cấp học bổng theo quỹ và kết quả rèn luyện/học tập, không quy định định mức tiền mặt cụ thể theo từng năm học.",
            "gold": []
        },
        {
            "id": "q_dev_unans_02",
            "split": "dev",
            "question": "Sinh viên ĐHQGHN có chứng chỉ HSK 6 tiếng Trung thì được miễn nộp toàn bộ học phí toàn khóa đúng không?",
            "expected_answer": "Không đủ bằng chứng để trả lời.",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Quy chế chỉ có điều khoản công nhận chuẩn đầu ra/miễn học phần ngoại ngữ, hoàn toàn không có chính sách miễn 100% học phí toàn khóa cho chứng chỉ HSK 6.",
            "gold": []
        },
        {
            "id": "q_test_unans_01",
            "split": "test",
            "question": "ĐHQGHN có cho phép sinh viên mang thú cưng vào ký túc xá nếu có giấy tiêm phòng không?",
            "expected_answer": "Không đủ bằng chứng để trả lời.",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Quy chế công tác sinh viên chỉ quy định nội trú an ninh trật tự và vệ sinh, không có điều khoản cho phép mang thú cưng vào khu nội trú.",
            "gold": []
        },
        {
            "id": "q_test_unans_02",
            "split": "test",
            "question": "Hạn chót nộp hồ sơ xin chuyển trường từ đại học ngoài vào ĐHQGHN trong học kỳ 1 năm học 2025-2026 là ngày nào?",
            "expected_answer": "Không đủ bằng chứng để trả lời.",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Quy chế đào tạo chỉ quy định thủ tục và điều kiện chuyển trường chung, không công bố ngày cụ thể hạn chót nộp hồ sơ của năm học 2025-2026.",
            "gold": []
        }
    ]
    
    for u in unanswerable:
        formatted_questions.append(u)
        agent_cases.append({
            "id": u["id"],
            "split": u["split"],
            "question": u["question"],
            "answerable": False,
            "expected_behavior": "search_and_abstain"
        })
        
    data_dir.mkdir(parents=True, exist_ok=True)
    
    q_file = data_dir / "questions.json"
    q_file.write_text(json.dumps(formatted_questions, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Also create answerable-only questions file for baseline.py (which requires gold for all items)
    ans_questions = [q for q in formatted_questions if q.get("answerable")]
    ans_q_file = data_dir / "answerable_questions.json"
    ans_q_file.write_text(json.dumps(ans_questions, ensure_ascii=False, indent=2), encoding="utf-8")

    cases_file = data_dir / "cases.json"
    cases_file.write_text(json.dumps(agent_cases, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"Total benchmark questions: {len(formatted_questions)}")
    dev_count = sum(1 for q in formatted_questions if q["split"] == "dev")
    test_count = sum(1 for q in formatted_questions if q["split"] == "test")
    print(f"Dev questions: {dev_count} (16 answerable + 2 unanswerable)")
    print(f"Test questions: {test_count} (6 answerable + 2 unanswerable)")
    print(f"Saved to {q_file}, {ans_q_file}, and {cases_file}")


if __name__ == "__main__":
    prepare_benchmark()
