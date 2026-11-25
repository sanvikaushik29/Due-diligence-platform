import os, json
from openai import OpenAI
from app.services.vector_store import retrieve

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a due-diligence assistant. Answer ONLY using the provided context chunks.
Every factual claim in your answer must be traceable to a specific chunk.
If the context doesn't contain enough information to answer, say so explicitly — never guess or infer beyond what's given.
Keep answers concise and direct."""

def answer_query(session_id: str, message: str, history: list[dict]) -> tuple[str, list[dict]]:
    chunks = retrieve(session_id, message)
    if not chunks:
        return "I don't have enough indexed information to answer that. Try uploading and processing documents first.", []

    context_text = "\n\n".join(
        f"[{i+1}] ({c['source_type']}, {c['filename']} p.{c['page']}): {c['text']}"
        for i, c in enumerate(chunks)
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:  # keep recent context bounded
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({
        "role": "user",
        "content": f"Context:\n{context_text}\n\nQuestion: {message}",
    })

    resp = client.chat.completions.create(model="gpt-4o", messages=messages, max_tokens=600)
    answer = resp.choices[0].message.content

    citations = [
        {"filename": c["filename"], "page": c["page"], "raw_text": c["raw_text"]}
        for c in chunks
    ]
    return answer, citations

def generate_opening_summary(risk: dict, consistency: dict) -> str:
    """Deterministic-ish: built from real flags, LLM only phrases it — doesn't invent findings."""
    flags = risk.get("flags", [])
    discrepancy_count = len(consistency.get("discrepancies", []))
    unsupported_count = len(consistency.get("unsupported_claims", []))

    if not flags and discrepancy_count == 0:
        return "I've reviewed the uploaded documents and found no significant discrepancies or risk flags. Ask me anything about the findings."

    top_flags = sorted(flags, key=lambda f: {"high": 0, "medium": 1, "low": 2}[f["severity"]])[:3]
    flags_text = "\n".join(f"- {f['rule_name']}: {f['description']}" for f in top_flags)

    prompt = f"""Write a 3-4 sentence opening summary for a due-diligence chat, based only on this data:

Top risk/discrepancy flags:
{flags_text}

Total discrepancies found: {discrepancy_count}
Total unsupported claims: {unsupported_count}

Do not invent any findings not listed above. Be direct and specific."""

    resp = client.chat.completions.create(
        model="gpt-4o", max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content