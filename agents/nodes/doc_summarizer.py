"""3.1 Doc summarizer — system-architecture.md Section 7. Reads the
uploaded document and produces a summary for the deal's Analyst Lead
pipeline. First node in the gate: 3.2 risk_flagger reads its output."""

from agents.adapters.model_adapter import call_model
from agents.documents import build_content_block, fetch_document
from agents.retry import with_retry
from agents.state import AnalystState

SUMMARY_PROMPT = (
    "You are the Analyst Lead's document summarizer for an M&A due diligence "
    "review. Summarize this document for an analyst: cover the key financial "
    "figures, notable risks or red flags, and any items that appear missing "
    "or outstanding. Be concrete — cite specific numbers and clauses where "
    "present. Keep it to a few tight paragraphs, not a bullet dump."
)


def _run_once(document_id: str) -> str:
    # fetch_document is inside the retried callable deliberately — any
    # failure in this node (fetch or model call) must convert to NodeFailure,
    # not leak a raw exception past the bounded-retry boundary (AGENT.md
    # Section 10; this is what phase2-007's end-to-end test caught).
    content, _filename, media_type = fetch_document(document_id)

    response = call_model(
        "doc_summarizer",
        messages=[
            {
                "role": "user",
                "content": [
                    build_content_block(content, media_type),
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


def doc_summarizer(state: AnalystState) -> AnalystState:
    summary = with_retry("doc_summarizer", lambda: _run_once(state["document_id"]))
    return {**state, "summary": summary}
