"""4.1 Contract summarizer — system-architecture.md Section 8. Runs on
ingest, alongside 4.2 clause_extractor (both consume the same raw
contract, no dependency between them — unlike the Analyst Lead's gated
3.1->3.2, these are an ingest-triggered pair per Figure 6)."""

import base64

from agents.adapters.model_adapter import call_model
from agents.documents import fetch_document
from agents.retry import with_retry

SUMMARY_PROMPT = (
    "You are the Contracts Lead's contract summarizer. Summarize this contract for "
    "an analyst: the parties, the core commercial terms, the term/renewal structure, "
    "and anything unusual (change-of-control provisions, exclusivity, non-standard "
    "liability terms). Keep it to a few tight paragraphs, not a bullet dump."
)


def _run_once(document_id: str) -> str:
    content, _filename, media_type = fetch_document(document_id)

    response = call_model(
        "contract_summarizer",
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
                    {"type": "text", "text": SUMMARY_PROMPT},
                ],
            }
        ],
        max_tokens=1536,
    )

    for block in response.content:
        if block.type == "text":
            return block.text

    raise ValueError(f"model returned no text block (stop_reason={response.stop_reason!r})")


def contract_summarizer(document_id: str) -> str:
    return with_retry("contract_summarizer", lambda: _run_once(document_id))
