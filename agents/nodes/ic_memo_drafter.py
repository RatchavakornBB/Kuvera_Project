"""3.3 IC memo drafter — system-architecture.md Section 7. Runs in parallel
with 3.4 pricing_advisor once the gate (3.1 -> 3.2) completes; both consume
the same summary + risk_flags. This is a core deliverable alongside
risk_flagger (AGENT.md Section 10) — its failure is never swallowed."""

from agents.adapters.model_adapter import call_model
from agents.retry import with_retry
from agents.state import AnalystState

MEMO_PROMPT = """You are the Analyst Lead's IC memo drafter for an M&A due diligence review.
Draft a concise internal investment committee memo in markdown from the summary and risk
flags below. Structure: a short deal overview paragraph, a "Key Financials" section, a
"Risks" section (group by severity), and a one-paragraph recommendation on next steps.
Ground every claim in the summary/risk flags given — do not invent figures.

SUMMARY:
{summary}

RISK FLAGS:
{risk_flags}
"""


def _format_risk_flags(risk_flags: list[dict]) -> str:
    if not risk_flags:
        return "(none identified)"
    return "\n".join(f"- [{r['severity']}] {r['description']}" for r in risk_flags)


def _call_and_parse(summary: str, risk_flags: list[dict]) -> str:
    prompt = MEMO_PROMPT.format(summary=summary, risk_flags=_format_risk_flags(risk_flags))
    response = call_model(
        "ic_memo_drafter",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
    )
    for block in response.content:
        if block.type == "text":
            return block.text
    raise ValueError(f"model returned no text block (stop_reason={response.stop_reason!r})")


def ic_memo_drafter(state: AnalystState) -> dict:
    ic_memo_draft = with_retry(
        "ic_memo_drafter", lambda: _call_and_parse(state["summary"], state.get("risk_flags", []))
    )
    return {"ic_memo_draft": ic_memo_draft}
