"""3.2 Risk flagger — system-architecture.md Section 7. Reads the summary
plus the original document and identifies missing information and key
investment risks. Only runs once 3.1 doc_summarizer has completed (the
gate — system-architecture.md Section 4.3).

Also carries the contradiction check: on re-analysis, if a prior stored
analysis exists for this deal, any figure/fact that contradicts it is
surfaced as an ordinary high-severity risk flag (unchanged, already-verified
behavior) AND recorded structurally via agents/contradictions.py — status
ranks (unconfirmed -> corroborated -> resolved/refuted) with real pgvector-
matched corroboration counting across re-analyses, since the flagged
description is freshly LLM-generated each time and never identical wording.
"""

from agents.adapters.model_adapter import call_model
from agents.analyses import get_last_analysis
from agents.contradictions import record_contradiction
from agents.documents import build_content_block, fetch_document
from agents.knowledge import historical_precedent_context
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
                        "is_contradiction": {
                            "type": "boolean",
                            "description": "true ONLY for the one flag added specifically because it contradicts the prior stored analysis — omit or false for every ordinary risk flag",
                        },
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
    "describing the contradiction, with source_excerpt quoting the new document, and set "
    "is_contradiction: true on that flag (and only that flag). If nothing contradicts, do "
    "not add a flag for this.\n\nPRIOR SUMMARY:\n{prior_summary}"
)


def _record_flagged_contradictions(deal_id: str, risk_flags: list[dict]) -> None:
    # Best-effort, same reasoning as historical_precedent_context: this is
    # structured bookkeeping on top of an already-returned, already-correct
    # risk_flags list — a failure here must never invalidate the real output
    # the user is waiting on.
    for flag in risk_flags:
        if not flag.get("is_contradiction"):
            continue
        try:
            record_contradiction(deal_id, flag["description"], flag.get("source_excerpt", ""))
        except Exception:
            pass


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

    # Real Knowledge Agent retrieval (system-architecture.md Section 10.1) —
    # genuine pgvector search over past closed deals, not the lightweight
    # context-stuffing pattern used elsewhere in this codebase. Best-effort:
    # historical_precedent_context() swallows its own failures.
    instructions += historical_precedent_context(state["deal_id"], state["summary"])

    response = call_model(
        "risk_flagger",
        messages=[
            {
                "role": "user",
                "content": [
                    build_content_block(content, media_type),
                    {"type": "text", "text": f"NEW SUMMARY:\n{state['summary']}\n\n{instructions}"},
                ],
            }
        ],
        tools=[RISK_FLAGGER_TOOL],
        # Bumped from 4096, then again from 8192, after real /deals/{id}/analyze
        # runs repeatedly hit stop_reason='max_tokens' mid tool-call — extended
        # thinking + a document with many real findable risks + contradiction/
        # historical-precedent reasoning can push output well past what this was
        # originally tuned for. 16384 gives real headroom, not a guess.
        max_tokens=16384,
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_risk_flags":
            if "risk_flags" not in block.input:
                raise ValueError(f"tool_use input missing 'risk_flags' key: {block.input!r}")
            risk_flags = block.input["risk_flags"]
            _record_flagged_contradictions(state["deal_id"], risk_flags)
            return risk_flags

    raise ValueError(f"model did not call report_risk_flags (stop_reason={response.stop_reason!r})")


def risk_flagger(state: AnalystState) -> AnalystState:
    risk_flags = with_retry("risk_flagger", lambda: _run_once(state))
    return {**state, "risk_flags": risk_flags}
