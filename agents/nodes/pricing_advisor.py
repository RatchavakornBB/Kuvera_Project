"""3.4 Pricing advisor — system-architecture.md Section 7. Runs in
parallel with 3.3 ic_memo_drafter. Explicitly secondary, best-effort
(AGENT.md Section 10 / Section 11 invariant): its failure must never
block or degrade the response from doc_summarizer -> risk_flagger ->
ic_memo_drafter. On failure after retries, this node swallows the
NodeFailure itself and returns pricing_note=None rather than raising —
the one place in the whole pipeline where a failure IS caught here
rather than propagated, and that's deliberate, not an oversight."""

import logging

from agents.adapters.model_adapter import call_model
from agents.errors import NodeFailure
from agents.knowledge import historical_precedent_context
from agents.retry import with_retry
from agents.state import AnalystState

logger = logging.getLogger("agents")

PRICING_PROMPT = """You are the Analyst Lead's pricing advisor for an M&A due diligence review.
Based on the summary and risk flags below, suggest indicative pricing or commercial terms
ONLY if the summary contains enough real financial data (e.g. revenue, margin, growth) to
ground a suggestion. If the data is insufficient, say so plainly instead of guessing — do
not invent a number. Keep it to one short paragraph.

SUMMARY:
{summary}

RISK FLAGS:
{risk_flags}
{precedent}
"""


def _format_risk_flags(risk_flags: list[dict]) -> str:
    if not risk_flags:
        return "(none identified)"
    return "\n".join(f"- [{r['severity']}] {r['description']}" for r in risk_flags)


def _call_and_parse(deal_id: str, summary: str, risk_flags: list[dict]) -> str:
    # Real Knowledge Agent retrieval (system-architecture.md Section 10.1) —
    # genuine pgvector search over past closed deals' pricing/outcome
    # precedent. Best-effort: swallows its own failures, same as risk_flagger.
    precedent = historical_precedent_context(deal_id, summary)
    prompt = PRICING_PROMPT.format(summary=summary, risk_flags=_format_risk_flags(risk_flags), precedent=precedent)
    response = call_model(
        "pricing_advisor",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    for block in response.content:
        if block.type == "text":
            return block.text
    raise ValueError(f"model returned no text block (stop_reason={response.stop_reason!r})")


def pricing_advisor(state: AnalystState) -> dict:
    try:
        pricing_note = with_retry(
            "pricing_advisor",
            lambda: _call_and_parse(state["deal_id"], state["summary"], state.get("risk_flags", [])),
        )
        return {"pricing_note": pricing_note}
    except NodeFailure as e:
        logger.warning("pricing_advisor degraded gracefully: %s", e)
        return {"pricing_note": None, "pricing_error": e.to_dict()}
