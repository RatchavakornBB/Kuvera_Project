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

from agents.adapters.model_adapter import call_model
from agents.chat_memory import chat_history_context
from agents.company_research import get_current_company_research
from agents.deal_context import build_deal_context
from agents.industry_brief import get_current_industry_brief
from agents.knowledge import get_deal_industry
from agents.retry import with_retry

ANSWER_TOOL = {
    "name": "answer_question",
    "description": "Answer the user's question about this deal, grounded in the provided data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Which records the answer drew from, e.g. 'Milestone: NDA signed', 'Document: FY2025 audited financial statements'",
            },
        },
        "required": ["answer", "sources"],
    },
}

SYSTEM_PROMPT = (
    "You are Concierge, the Kuvera Assistant's internal Q&A agent. You answer questions "
    "about EXACTLY ONE deal. The DEAL DATA given with each question is everything known "
    "about that deal — ground your answer only in it, plus the general industry "
    "background below if one is provided. If the answer isn't contained in the deal data, "
    "say so plainly rather than guessing. Never reference any deal other than the one "
    "described in DEAL DATA — you have no knowledge of any other deal. Call "
    "answer_question with your result."
)


def _run_once(deal_id: str, question: str) -> dict:
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
        tools=[ANSWER_TOOL],
        system=system,
        max_tokens=1024,
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "answer_question":
            if "answer" not in block.input:
                raise ValueError(f"tool_use input missing 'answer' key: {block.input!r}")
            return {"answer": block.input["answer"], "sources": block.input.get("sources", [])}

    raise ValueError(f"model did not call answer_question (stop_reason={response.stop_reason!r})")


def concierge_qa(deal_id: str, question: str) -> dict:
    return with_retry("concierge_qa", lambda: _run_once(deal_id, question))
