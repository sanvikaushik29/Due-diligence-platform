import os, json
import numpy as np
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBED_MODEL = "text-embedding-3-small"
STORE_DIR = "./local_vector_store"
os.makedirs(STORE_DIR, exist_ok=True)

def _embed(texts: list[str]) -> list[list[float]]:
    resp = openai_client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def _session_path(session_id: str) -> str:
    return os.path.join(STORE_DIR, f"{session_id}.json")

def build_corpus(extractions: list[dict], metrics: list[dict], consistency: dict, risk: dict) -> list[dict]:
    """Each chunk: {text, filename, page, raw_text, source_type}"""
    chunks = []

    for ext in extractions:
        for m in ext.get("metrics", []):
            chunks.append({
                "text": f"{m['metric_name']}: {m['value']} {m['unit']} ({m.get('period') or 'no period'}). Context: {m['raw_text']}",
                "filename": ext["filename"], "page": m["source_page"],
                "raw_text": m["raw_text"], "source_type": "metric",
            })
        for c in ext.get("claims", []):
            chunks.append({
                "text": f"Claim ({c['category']}): {c['claim_text']}. Supported by data: {c['has_supporting_data']}",
                "filename": ext["filename"], "page": c["source_page"],
                "raw_text": c["raw_text"], "source_type": "claim",
            })

    for d in consistency.get("discrepancies", []):
        for v in d["values"]:
            chunks.append({
                "text": f"Discrepancy in {d['canonical_name']} ({d['severity']} severity, {d['max_delta_percent']}% delta): {v['raw_text']}",
                "filename": v["filename"], "page": v["page"],
                "raw_text": v["raw_text"], "source_type": "discrepancy",
            })

    for f in risk.get("flags", []):
        for e in f["evidence"]:
            chunks.append({
                "text": f"Risk flag - {f['rule_name']} ({f['severity']}): {f['description']}",
                "filename": e["filename"], "page": e["page"],
                "raw_text": e["raw_text"], "source_type": "risk_flag",
            })

    return chunks

def index_session(session_id: str, extractions: list[dict], metrics: list[dict], consistency: dict, risk: dict) -> int:
    chunks = build_corpus(extractions, metrics, consistency, risk)
    if not chunks:
        return 0

    embeddings = _embed([c["text"] for c in chunks])
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    with open(_session_path(session_id), "w") as f:
        json.dump(chunks, f)

    return len(chunks)

def retrieve(session_id: str, query: str, top_k: int = 6) -> list[dict]:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return []

    with open(path) as f:
        chunks = json.load(f)
    if not chunks:
        return []

    query_vector = np.array(_embed([query])[0])
    matrix = np.array([c["embedding"] for c in chunks])

    # cosine similarity
    query_norm = query_vector / np.linalg.norm(query_vector)
    matrix_norm = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
    scores = matrix_norm @ query_norm

    top_indices = np.argsort(scores)[::-1][:top_k]
    return [{k: v for k, v in chunks[i].items() if k != "embedding"} for i in top_indices]