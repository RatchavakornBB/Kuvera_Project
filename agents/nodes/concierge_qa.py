"""2.1 Concierge Q&A — system-architecture.md Section 6. Answers questions
grounded ONLY in one deal's data (AGENT.md Section 11: never blend data
across deals — enforced structurally by agents/deal_context.py, which
never fetches another deal's rows in the first place)."""

from agents.adapters.model_adapter import call_model
from agents.deal_context import build_deal_context
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
    "about EXACTLY ONE deal — the data below is everything known about that deal and "
    "nothing else. Ground your answer only in this data. If the answer isn't contained "
    "in the data, say so plainly rather than guessing. Never reference any deal other "
    "than the one described below — you have no knowledge of any other deal. Call "
    "answer_question with your result."
)


def _run_once(deal_id: str, question: str) -> dict:
    context = build_deal_context(deal_id)

    response = call_model(
        "concierge_qa",
        messages=[
            {
                "role": "user",
                "content": f"{SYSTEM_PROMPT}\n\nDEAL DATA:\n{context}\n\nQUESTION: {question}",
            }
        ],
        tools=[ANSWER_TOOL],
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
