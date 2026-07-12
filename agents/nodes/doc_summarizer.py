"""3.1 Doc summarizer — system-architecture.md Section 7. Reads the
uploaded document and produces a summary for the deal's Analyst Lead
pipeline. First node in the gate: 3.2 risk_flagger reads its output."""

import base64

from agents.adapters.model_adapter import call_model
from agents.documents import fetch_document
from agents.state import AnalystState

SUMMARY_PROMPT = (
    "You are the Analyst Lead's document summarizer for an M&A due diligence "
    "review. Summarize this document for an analyst: cover the key financial "
    "figures, notable risks or red flags, and any items that appear missing "
    "or outstanding. Be concrete — cite specific numbers and clauses where "
    "present. Keep it to a few tight paragraphs, not a bullet dump."
)


def doc_summarizer(state: AnalystState) -> AnalystState:
    content, _filename, media_type = fetch_document(state["document_id"])

    response = call_model(
        "doc_summarizer",
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
        max_tokens=1024,
    )

    summary = response.content[0].text
    return {**state, "summary": summary}
