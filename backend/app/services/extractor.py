import os, json
from openai import OpenAI
from app.models.schemas import DocType

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EXTRACTION_SCHEMA = {
    "name": "record_extraction",
    "schema": {
        "type": "object",
        "properties": {
            "metrics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric_name": {"type": "string"},
                        "value": {"type": "number"},
                        "unit": {"type": "string"},
                        "period": {"type": ["string", "null"]},
                        "raw_text": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["metric_name", "value", "unit", "period", "raw_text", "confidence"],
                    "additionalProperties": False,
                },
            },
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_text": {"type": "string"},
                        "category": {"type": "string", "enum": ["traction", "market", "team", "product", "other"]},
                        "raw_text": {"type": "string"},
                        "has_supporting_data": {"type": "boolean"},
                    },
                    "required": ["claim_text", "category", "raw_text", "has_supporting_data"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["metrics", "claims"],
        "additionalProperties": False,
    },
    "strict": True,
}

def classify_doc_type(first_page_text: str) -> DocType:
    prompt = f"""Classify this document's opening page as one of:
pitch_deck, financial_statement, cap_table, unknown.
Reply with only the label.

Text:
{first_page_text[:1500]}"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=20,
        messages=[{"role": "user", "content": prompt}],
    )
    label = resp.choices[0].message.content.strip().lower()
    return DocType(label) if label in DocType._value2member_map_ else DocType.UNKNOWN

def extract_page(page_text: str, doc_type: DocType, page_number: int) -> dict:
    system = f"""You extract financial metrics and factual claims from a {doc_type.value} page.
Only extract what is explicitly stated — never infer or calculate missing values.
Every metric and claim must include the exact raw_text it came from."""

    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Page {page_number} text:\n\n{page_text}"},
        ],
        response_format={"type": "json_schema", "json_schema": EXTRACTION_SCHEMA},
    )
    return json.loads(resp.choices[0].message.content)