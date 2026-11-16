"""Index embeddings for Vinamilk Annual Report chunks with safe rate-limiting."""
import hashlib
import json
import logging
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

env_paths = [Path(".env"), Path("../.env"), Path("E:/AI_vin20k/K5-L3-Day06-DataIngestionEngineering-main/K5-L3-Day06-DataIngestionEngineering-main/starter/.env")]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        break

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found!")

chunks_path = Path("data/advanced_chunks.json")
cache_db = Path("data/advanced_embeddings_cache.sqlite")

chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
logger.info(f"Loaded {len(chunks)} chunks.")

conn = sqlite3.connect(cache_db)
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS cache (
        text_hash TEXT PRIMARY KEY,
        vector_json TEXT NOT NULL
    );
""")
conn.commit()

missing = []
for c in chunks:
    text = c["text"]
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cur.execute("SELECT vector_json FROM cache WHERE text_hash=?", (h,))
    row = cur.fetchone()
    if not row:
        missing.append((c["id"], text, h))

logger.info(f"Missing embeddings: {len(missing)} / {len(chunks)}")

model_name = "models/gemini-embedding-001"
batch_size = 15

for i in range(0, len(missing), batch_size):
    batch = missing[i:i + batch_size]
    batch_idx = i // batch_size + 1
    total_batches = (len(missing) + batch_size - 1) // batch_size
    logger.info(f"Embedding batch {batch_idx}/{total_batches} ({len(batch)} chunks)...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:batchEmbedContents?key={api_key}"
    req_body = {
        "requests": [
            {
                "model": model_name,
                "content": {"parts": [{"text": item[1]}]},
                "outputDimensionality": 768
            }
            for item in batch
        ]
    }
    
    data = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                embeddings = resp_json.get("embeddings", [])
                for (cid, text, h), emb in zip(batch, embeddings):
                    vec = emb.get("values", [])
                    cur.execute("INSERT OR REPLACE INTO cache (text_hash, vector_json) VALUES (?, ?)", (h, json.dumps(vec)))
                conn.commit()
                break
        except Exception as e:
            wait_time = 12 * (attempt + 1)
            logger.warning(f"Batch {batch_idx} attempt {attempt + 1} failed: {e}. Waiting {wait_time}s...")
            time.sleep(wait_time)
            
    time.sleep(2.5)

logger.info("All embeddings generated and cached successfully!")
cur.execute("SELECT COUNT(*) FROM cache")
total_cached = cur.fetchone()[0]
logger.info(f"Total entries in cache: {total_cached}")
conn.close()
