"""3.2 Risk flagger — system-architecture.md Section 7. Reads the summary
plus the original document and identifies missing information and key
investment risks. Only runs once 3.1 doc_summarizer has completed (the
gate — system-architecture.md Section 4.3).

Also carries the lightweight contradiction check (timeline Section 6 Phase
2, scoped down from Section 10.5): on re-analysis, if a prior stored
analysis exists for this deal, any figure/fact that contradicts it is
surfaced as an ordinary high-severity risk flag — no confidence scoring or
hypothesis status, just a visible flag for the user to resolve.
"""

import base64

from agents.adapters.model_adapter import call_model
from agents.analyses import get_last_analysis
from agents.documents import fetch_document
from agents.retry import with_retry
from agents.state import AnalystState

RISK_FLAGGER_TOOL = {
    "name": "report_risk_flags",
    "description": "Report the structured list of risk flags identified for this deal.",
    "input_schema": {
        "type": "object",
        "properties": {
            "risk_flags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["high", "medium"]},
                        "description": {"type": "string"},
                        "source_excerpt": {"type": "string"},
                    },
                    "required": ["severity", "description", "source_excerpt"],
                },
            }
        },
        "required": ["risk_flags"],
    },
}

BASE_INSTRUCTIONS = (
    "You are the Analyst Lead's risk flagger for an M&A due diligence review. "
    "Given the summary below and the original source document, identify missing "
    "information and key investment risks. For each risk: pick 'high' severity for "
    "anything that could materially affect deal value or structure (e.g. "
    "change-of-control clauses, undisclosed related-party transactions, concentration "
    "risk above ~30%), 'medium' for everything else worth flagging. Quote a short "
    "source_excerpt from the document for each flag. Call report_risk_flags with the "
    "result."
)

CONTRADICTION_INSTRUCTIONS = (
    "\n\nThis deal has a prior stored analysis. Compare the new summary below against "
    "the PRIOR summary that follows it. If any key figure or fact changed between the "
    "two versions (e.g. a revenue number, a risk that disappeared or a new one that "
    "appeared, a changed clause), add ONE additional 'high' severity risk flag "
    "describing the contradiction, with source_excerpt quoting the new document. If "
    "nothing contradicts, do not add a flag for this.\n\nPRIOR SUMMARY:\n{prior_summary}"
)


def _run_once(state: AnalystState) -> list:
    # fetch_document + get_last_analysis are inside the retried callable
    # deliberately — any failure in this node must convert to NodeFailure,
    # not leak past the bounded-retry boundary (same fix as doc_summarizer,
    # AGENT.md Section 10; caught by phase2-007's end-to-end error test).
    content, _filename, media_type = fetch_document(state["document_id"])

    instructions = BASE_INSTRUCTIONS
    prior = get_last_analysis(state["deal_id"])
    if prior:
        instructions += CONTRADICTION_INSTRUCTIONS.format(prior_summary=prior["summary"])

    response = call_model(
        "risk_flagger",
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
                    {"type": "text", "text": f"NEW SUMMARY:\n{state['summary']}\n\n{instructions}"},
                ],
            }
        ],
        tools=[RISK_FLAGGER_TOOL],
        max_tokens=4096,
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_risk_flags":
            if "risk_flags" not in block.input:
                raise ValueError(f"tool_use input missing 'risk_flags' key: {block.input!r}")
            return block.input["risk_flags"]

    raise ValueError(f"model did not call report_risk_flags (stop_reason={response.stop_reason!r})")


def risk_flagger(state: AnalystState) -> AnalystState:
    risk_flags = with_retry("risk_flagger", lambda: _run_once(state))
    return {**state, "risk_flags": risk_flags}
