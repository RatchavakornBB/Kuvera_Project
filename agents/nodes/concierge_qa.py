"""2.1 Concierge Q&A — system-architecture.md Section 6. Answers questions
grounded ONLY in one deal's data (AGENT.md Section 11: never blend data
across deals — enforced structurally by agents/deal_context.py, which
never fetches another deal's rows in the first place).

The current Industry Brief for this deal's industry (agents/industry_brief.py's
periodically-refreshed cache, Section 10.1's "fine-tuning-style" storage) and
the current Company Research note for this deal's own target company
(agents/company_research.py, refreshed daily per-deal) are both passed via
`system`, not stuffed into the per-deal user content — they're the parts of
this call that are actually stable across many consecutive calls to this
agent, so they're the parts worth marking as a cache breakpoint
(call_model's cache_control on the system block)."""

from typing import Callable

from agents.adapters.model_adapter import call_model
from agents.chat_memory import chat_history_context
from agents.company_research import get_current_company_research
from agents.deal_context import build_deal_context
from agents.industry_brief import get_current_industry_brief
from agents.knowledge import get_deal_industry
from agents.retry import with_retry

# Sources come back through a tool call so they stay structured, but the answer
# itself is ordinary streamed prose (not a tool field) — that's what lets the
# reply type out live over the /chat WebSocket instead of materializing all at
# once. cite_sources is NOT required: a model that answers in prose and skips it
# still gives a valid answer with no sources, which is fine.
CITE_SOURCES_TOOL = {
    "name": "cite_sources",
    "description": (
        "After writing your answer, call this once with the deal records the answer drew "
        "from, e.g. 'Milestone: NDA signed', 'Document: FY2025 audited financial statements'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["sources"],
    },
}

SYSTEM_PROMPT = (
    "You are Concierge, the Kuvera Assistant's internal Q&A agent. You answer questions "
    "about EXACTLY ONE deal. The DEAL DATA given with each question is everything known "
    "about that deal — ground your answer only in it, plus the general industry "
    "background below if one is provided. If the answer isn't contained in the deal data, "
    "say so plainly rather than guessing. Never reference any deal other than the one "
    "described in DEAL DATA — you have no knowledge of any other deal. Write your answer "
    "as plain prose for the user, then call cite_sources with the records you used."
)


def _run_once(deal_id: str, question: str, on_delta: Callable[[str], None] | None = None) -> dict:
    context = build_deal_context(deal_id) + chat_history_context(deal_id, question)

    industry = get_deal_industry(deal_id)
    brief = get_current_industry_brief(industry) if industry else None
    system = SYSTEM_PROMPT
    if brief:
        system += f"\n\nINDUSTRY BACKGROUND ({brief['industry']}, not deal-specific): {brief['summary']}"

    company_research = get_current_company_research(deal_id)
    if company_research:
        system += (
            f"\n\nCOMPANY RESEARCH ({company_research['company_name']}, refreshed periodically): "
            f"{company_research['summary']}"
        )

    response = call_model(
        "concierge_qa",
        messages=[{"role": "user", "content": f"DEAL DATA:\n{context}\n\nQUESTION: {question}"}],
        tools=[CITE_SOURCES_TOOL],
        system=system,
        max_tokens=1024,
        on_delta=on_delta,
    )

    answer = "".join(block.text for block in response.content if block.type == "text").strip()
    sources: list[str] = []
    for block in response.content:
        if block.type == "tool_use" and block.name == "cite_sources":
            sources = block.input.get("sources", [])

    # The answer is now free text, so "model produced nothing usable" is the only
    # real failure — a bare cite_sources call with no prose. Raise so with_retry
    # gets one more attempt rather than returning an empty bubble to the user.
    if not answer:
        raise ValueError(f"model produced no answer text (stop_reason={response.stop_reason!r})")
    return {"answer": answer, "sources": sources}


def concierge_qa(deal_id: str, question: str, on_delta: Callable[[str], None] | None = None) -> dict:
    return with_retry("concierge_qa", lambda: _run_once(deal_id, question, on_delta))
