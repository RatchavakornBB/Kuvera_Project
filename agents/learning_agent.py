"""Learning Agent (system-architecture.md Section 10.3) — "a separate background agent from
Knowledge Agent... continuously ingests the outside world." On-demand for now (no scheduler exists
yet in this codebase); phase6's Key-date notifier task should retrofit this onto a real interval
too, same as agents/industry_brief.py's Briefs.

Uses Claude's real web_search server tool for genuine current research — not fabricated
commentary. Optionally proposes a real skill.md addition through the exact same approval queue
(pending_changes) a human editing the Admin Skills tab uses — the doc's own framing: "always
subject to the same eval + admin approval gate as any other agent change." Most cycles should
propose nothing; the model only proposes when it found something genuinely specific and actionable,
not on every run."""

from typing import Any

from agents.adapters.model_adapter import call_model
from agents.agent_config import list_agent_configs, propose_skill_addition
from agents.db import get_client
from agents.retry import with_retry

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}

CATEGORY_TOPICS = {
    "ma_training_data": "M&A deal patterns and transaction structures",
    "prediction_models": "mathematical/financial prediction models relevant to M&A valuation and risk modeling",
    "market_news": "current business, economic, and stock-market news",
    "law_regulation": "law and regulatory updates relevant to M&A due diligence",
}

DIGEST_PROMPT = """You are the Learning Agent, continuously researching the outside world for an
M&A deal-ops platform. Research {topic_desc}, specifically: {topic}. Use web search for current,
real information — cite what you actually find, a few paragraphs, no generic filler.

Then decide: does this research surface something CONCRETE and SPECIFIC enough to warrant adding
ONE real instruction to a specific agent's skill.md? Only propose a skill update if you have a
genuinely specific, actionable instruction grounded in what you found — most research cycles
should NOT propose anything; omit propose_skill_update entirely if nothing concrete surfaced.
Call report_digest with your result."""


def _digest_tool(agent_names: list[str]) -> dict[str, Any]:
    return {
        "name": "report_digest",
        "description": "Report the research digest and, only if warranted, propose a specific skill improvement for one agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "digest": {"type": "string", "description": "The research digest — cite what was actually found"},
                "propose_skill_update": {
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string", "enum": agent_names},
                        "additional_skill_instruction": {
                            "type": "string",
                            "description": "One or two sentences to ADD to this agent's skill.md, grounded specifically in what was just researched",
                        },
                        "rationale": {"type": "string"},
                    },
                    "required": ["agent_name", "additional_skill_instruction", "rationale"],
                },
            },
            "required": ["digest"],
        },
    }


def run_learning_cycle(category: str, topic: str) -> dict[str, Any]:
    if category not in CATEGORY_TOPICS:
        raise ValueError(f"Invalid category: {category!r}")

    agent_names = [c["agent_name"] for c in list_agent_configs() if c["agent_name"] != "learning_agent"]

    def _call() -> dict[str, Any]:
        response = call_model(
            "learning_agent",
            messages=[
                {
                    "role": "user",
                    "content": DIGEST_PROMPT.format(topic_desc=CATEGORY_TOPICS[category], topic=topic),
                }
            ],
            tools=[WEB_SEARCH_TOOL, _digest_tool(agent_names)],
            max_tokens=4096,
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "report_digest":
                return block.input
        raise ValueError(f"model did not call report_digest (stop_reason={response.stop_reason!r})")

    result = with_retry("learning_agent", _call)
    digest = result.get("digest", "")
    proposal = result.get("propose_skill_update")

    proposed_change_id = None
    if proposal:
        instruction = f"{proposal['additional_skill_instruction']} (learned: {proposal['rationale']})"
        change = propose_skill_addition(proposal["agent_name"], instruction)
        if change:
            proposed_change_id = change["id"]

    client = get_client()
    res = (
        client.table("learning_digests")
        .insert({"category": category, "topic": topic, "digest": digest, "proposed_change_id": proposed_change_id})
        .execute()
    )
    return res.data[0]


def list_digests() -> list[dict[str, Any]]:
    client = get_client()
    return client.table("learning_digests").select("*").order("created_at", desc=True).execute().data
