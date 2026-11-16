"""Advanced Indexer for Vinamilk Annual Report (112 pages).
Extracts text, identifies tables/charts/diagrams, chunks all 112 pages,
and prepares data/advanced_chunks.json with unified schema ('id'/'chunk_id', 'text'/'content').
"""
import pypdf
import json
import re
from pathlib import Path

def extract_advanced_chunks(pdf_path: str):
    reader = pypdf.PdfReader(pdf_path)
    chunks = []
    chunk_counter = 1

    table_pages = {11, 48, 49, 78, 85, 108, 109, 110, 111, 112}
    chart_pages = {7, 10, 12, 51, 52, 76, 86}
    diagram_pages = {8, 13, 14, 15, 16, 17, 33, 81}

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        raw_text = page.extract_text() or ""
        cleaned_text = re.sub(r"[ \t]+", " ", raw_text).strip()
        if not cleaned_text:
            continue

        # Determine element type
        if page_num in table_pages:
            elem_type = "table"
        elif page_num in chart_pages:
            elem_type = "chart"
        elif page_num in diagram_pages:
            elem_type = "diagram"
        else:
            if any(k in cleaned_text.lower() for k in ["bảng", "hệ số", "triệu vnd", "stt", "báo cáo tài chính"]):
                elem_type = "table"
            elif any(k in cleaned_text.lower() for k in ["sơ đồ", "cơ cấu tổ chức", "cấu trúc tập đoàn"]):
                elem_type = "diagram"
            elif any(k in cleaned_text.lower() for k in ["biểu đồ", "tăng trưởng", "%"]):
                elem_type = "chart"
            else:
                elem_type = "text"

        header_prefix = f"[Vinamilk AR 2025 - Trang {page_num} - {elem_type.upper()}]\n"

        # If table, diagram, chart or <= 1200 chars, keep intact
        if elem_type in ["table", "diagram", "chart"] or len(cleaned_text) <= 1200:
            chunk_id = f"vnm_p{page_num:03d}_{chunk_counter:03d}"
            content = header_prefix + cleaned_text
            chunks.append({
                "id": chunk_id,
                "chunk_id": chunk_id,
                "document_id": "vinamilk_annual_report",
                "page": page_num,
                "element_type": elem_type,
                "text": content,
                "content": content
            })
            chunk_counter += 1
        else:
            lines = [l.strip() for l in cleaned_text.split("\n") if l.strip()]
            cur_lines = []
            cur_len = 0
            for line in lines:
                cur_lines.append(line)
                cur_len += len(line) + 1
                if cur_len >= 800:
                    chunk_text = "\n".join(cur_lines)
                    chunk_id = f"vnm_p{page_num:03d}_{chunk_counter:03d}"
                    content = header_prefix + chunk_text
                    chunks.append({
                        "id": chunk_id,
                        "chunk_id": chunk_id,
                        "document_id": "vinamilk_annual_report",
                        "page": page_num,
                        "element_type": elem_type,
                        "text": content,
                        "content": content
                    })
                    chunk_counter += 1
                    cur_lines = cur_lines[-3:]
                    cur_len = sum(len(l) + 1 for l in cur_lines)

            if cur_lines and cur_len > 100:
                chunk_text = "\n".join(cur_lines)
                chunk_id = f"vnm_p{page_num:03d}_{chunk_counter:03d}"
                content = header_prefix + chunk_text
                chunks.append({
                    "id": chunk_id,
                    "chunk_id": chunk_id,
                    "document_id": "vinamilk_annual_report",
                    "page": page_num,
                    "element_type": elem_type,
                    "text": content,
                    "content": content
                })
                chunk_counter += 1

    return chunks

if __name__ == "__main__":
    pdf_file = "data/vinamilk_annual_report.pdf"
    chunks = extract_advanced_chunks(pdf_file)
    print(f"Total extracted chunks from 112 pages: {len(chunks)}")
    
    counts = {}
    for c in chunks:
        counts[c["element_type"]] = counts.get(c["element_type"], 0) + 1
    print(f"Element types breakdown: {counts}")

    with open("data/advanced_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print("Saved to data/advanced_chunks.json")
