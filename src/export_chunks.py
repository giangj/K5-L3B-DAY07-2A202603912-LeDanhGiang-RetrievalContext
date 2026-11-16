"""Export Day 6 corpus pages into Day 7 data/chunks.json format."""
import json
import logging
import re
import unicodedata
from pathlib import Path
import pypdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ").replace("\u200b", "")
    cleaned_lines = []
    for line in text.split("\n"):
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        cleaned_lines.append(cleaned_line)
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_oversized_paragraph(para: str, max_size: int) -> list[str]:
    sentence_delimiters = re.split(r"(?<=[.!?;\n])\s+", para)
    pieces: list[str] = []
    current = ""
    for s in sentence_delimiters:
        s = s.strip()
        if not s:
            continue
        if len(s) > max_size:
            if current:
                pieces.append(current.strip())
                current = ""
            for i in range(0, len(s), max_size - 40):
                piece = s[i:i + max_size].strip()
                if piece:
                    pieces.append(piece)
        elif len(current) + len(s) + 1 <= max_size:
            current = f"{current} {s}" if current else s
        else:
            if current:
                pieces.append(current.strip())
            current = s
    if current:
        pieces.append(current.strip())
    return pieces


def by_paragraph(text: str, document_id: str, source: str, page: int, metadata: dict, max_size: int = 500) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    raw_paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not raw_paras:
        raw_paras = [text]

    normalized_paras: list[str] = []
    for p in raw_paras:
        if len(p) <= max_size:
            normalized_paras.append(p)
        else:
            normalized_paras.extend(_split_oversized_paragraph(p, max_size))

    chunks: list[dict] = []
    current_buf: list[str] = []
    current_len = 0
    idx = 0

    for p in normalized_paras:
        additional_len = len(p) + (2 if current_buf else 0)
        if current_buf and (current_len + additional_len > max_size):
            chunk_text = "\n\n".join(current_buf).strip()
            chunk_id = f"{document_id}_p{page}_para{idx}"
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "source_id": document_id,
                "source": source,
                "page": page,
                "metadata": {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": idx,
                }
            })
            idx += 1
            current_buf = [p]
            current_len = len(p)
        else:
            current_buf.append(p)
            current_len += additional_len

    if current_buf:
        chunk_text = "\n\n".join(current_buf).strip()
        chunk_id = f"{document_id}_p{page}_para{idx}"
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "source_id": document_id,
            "source": source,
            "page": page,
            "metadata": {
                **metadata,
                "chunk_id": chunk_id,
                "chunk_index": idx,
            }
        })
    return chunks


def export_corpus_chunks(data_dir: Path, output_file: Path) -> list[dict]:
    manifest_path = data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    all_chunks = []
    total_pages = 0

    for entry in manifest:
        source_id = entry["source_id"]
        pdf_name = Path(entry["source_path"]).name
        pdf_path = data_dir / pdf_name
        reader = pypdf.PdfReader(str(pdf_path))
        base_meta = entry.get("metadata_fields", {})

        for idx, page_obj in enumerate(reader.pages):
            page_num = idx + 1
            raw_text = page_obj.extract_text() or ""
            clean_text = normalize_text(raw_text)
            page_meta = {
                **base_meta,
                "document_id": source_id,
                "source": f"data/{pdf_name}",
                "page": page_num,
            }
            page_chunks = by_paragraph(
                clean_text,
                document_id=source_id,
                source=f"data/{pdf_name}",
                page=page_num,
                metadata=page_meta,
                max_size=500
            )
            all_chunks.extend(page_chunks)
            total_pages += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Exported %d chunks across %d pages to %s", len(all_chunks), total_pages, output_file)
    return all_chunks


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    output_chunks = data_dir / "chunks.json"
    export_corpus_chunks(data_dir, output_chunks)
