"""4.2 Clause extractor — system-architecture.md Section 8. Ingest-triggered
alongside 4.1 contract_summarizer, no dependency between them."""

import base64

from agents.adapters.model_adapter import call_model
from agents.documents import fetch_document
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


def _run_once(document_id: str) -> list[dict]:
    content, _filename, media_type = fetch_document(document_id)

    response = call_model(
        "clause_extractor",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.standard_b64encode(content).decode(),
                        },
                    },
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
            return block.input["clauses"]

    raise ValueError(f"model did not call report_clauses (stop_reason={response.stop_reason!r})")


def clause_extractor(document_id: str) -> list[dict]:
    return with_retry("clause_extractor", lambda: _run_once(document_id))
