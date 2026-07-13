"""4.2 Clause extractor — system-architecture.md Section 8. Ingest-triggered
alongside 4.1 contract_summarizer, no dependency between them."""

import json

from agents.adapters.model_adapter import call_model
from agents.documents import build_content_block, fetch_document
from agents.retry import with_retry

CLAUSE_TOOL = {
    "name": "report_clauses",
    "description": "Report the key clauses extracted from this contract.",
    "input_schema": {
        "type": "object",
        "properties": {
            "clauses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "Short clause type, e.g. 'Change of control', 'Term & renewal', 'Liability cap'"},
                        "text": {"type": "string", "description": "The clause itself, quoted or tightly paraphrased from the document"},
                    },
                    "required": ["label", "text"],
                },
            }
        },
        "required": ["clauses"],
    },
}

EXTRACT_PROMPT = (
    "You are the Contracts Lead's clause extractor. Extract the key clauses from this "
    "contract — term/renewal, termination, change-of-control, liability/indemnification, "
    "exclusivity, and any other clause a due-diligence analyst would need to know about. "
    "Call report_clauses with the result."
)


def _normalize_clauses(value: object) -> list[dict]:
    """Claude's tool_use output for an array-typed field is usually
    schema-conformant but not always — seen in real testing here returning a
    JSON-encoded string (itself wrapping a redundant {"clauses": [...]} dict)
    instead of the raw array, the same failure mode agents/knowledge.py's
    _normalize_field already defends against for object-typed fields."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    if isinstance(value, dict) and "clauses" in value:
        value = value["clauses"]
    return value if isinstance(value, list) else []


def _run_once(document_id: str) -> list[dict]:
    content, _filename, media_type = fetch_document(document_id)

    response = call_model(
        "clause_extractor",
        messages=[
            {
                "role": "user",
                "content": [
                    build_content_block(content, media_type),
                    {"type": "text", "text": EXTRACT_PROMPT},
                ],
            }
        ],
        tools=[CLAUSE_TOOL],
        max_tokens=2048,
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_clauses":
            if "clauses" not in block.input:
                raise ValueError(f"tool_use input missing 'clauses' key: {block.input!r}")
            return _normalize_clauses(block.input["clauses"])

    raise ValueError(f"model did not call report_clauses (stop_reason={response.stop_reason!r})")


def clause_extractor(document_id: str) -> list[dict]:
    return with_retry("clause_extractor", lambda: _run_once(document_id))
