"""Learning Agent (system-architecture.md Section 10.3) — "a separate background agent from
Knowledge Agent... continuously ingests the outside world." On-demand for now (no scheduler exists
yet in this codebase); phase6's Key-date notifier task should retrofit this onto a real interval
too, same as agents/industry_brief.py's Briefs.

Uses Claude's real web_search + web_fetch server tools (same pairing as agents/nodes/web_research.py
— search to find candidates, fetch to actually read them; a search snippet alone is never treated
as a finding). For the ma_training_data lane specifically, also cross-reads Knowledge Agent's
promoted knowledge_base records (agents/knowledge.py::list_knowledge — read-only, no tool call,
never written back to; that stays Knowledge Promoter's exclusive job) so an internal pattern can be
weighed against external market commentary rather than judged in isolation.

Optionally proposes a real skill.md addition through the exact same approval queue (pending_changes)
a human editing the Admin Skills tab uses — the doc's own framing: "always subject to the same eval
+ admin approval gate as any other agent change." The proposal bar itself (skill_self_creation) is
enforced as required fields on the report_digest tool call, not a separate loaded file — this
codebase has no runtime skill-loading-from-file mechanism anywhere else (skills live in
agent_configs.skill_content, authored via DB rows), so the checklist is operationalized the same
way every other structured decision in this system is: a tool schema the model must fill in, not
prose it can skim past. Most cycles should still propose nothing; the model only proposes when it
found something genuinely specific and actionable, not on every run."""

from typing import Any

from agents.adapters.model_adapter import call_model
from agents.agent_config import list_agent_configs, propose_skill_addition
from agents.db import get_client
from agents.knowledge import list_knowledge
from agents.retry import with_retry

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
WEB_FETCH_TOOL = {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 5}
WEB_FETCH_BETAS = ["web-fetch-2025-09-10"]

CATEGORY_TOPICS = {
    "ma_training_data": "M&A deal patterns and transaction structures",
    "prediction_models": "mathematical/financial prediction models relevant to M&A valuation and risk modeling",
    "market_news": "current business, economic, and stock-market news",
    "law_regulation": "law and regulatory updates relevant to M&A due diligence",
}

DIGEST_PROMPT = """You are the Learning Agent, continuously researching the outside world for an
M&A deal-ops platform. Research {topic_desc}, specifically: {topic}. Use web_search to find
candidates, then web_fetch the most promising results to read the actual content — a search
snippet is for triage only, never sufficient grounds for a finding on its own. Cite what you
actually find, a few paragraphs, no generic filler.{internal_context}

Then decide: does this research surface something CONCRETE and SPECIFIC enough to warrant adding
ONE real instruction to a specific agent's skill.md? Only call propose_skill_update if ALL of the
following hold — the same bar a human-authored skill change is held to, not a lower one:
  - a specific, concrete gap you can point to (an agent handled or would handle something wrong),
    not something that merely seems like it could theoretically matter
  - general enough to matter beyond one deal — a one-off oddity belongs in Knowledge Promoter's
    per-deal precedent, not a platform-wide skill change
  - a specific instruction you can state, not just "this agent should know more about X"
  - corroborated by more than one independent source, not a single speculative one
Most research cycles should NOT propose anything — omit propose_skill_update entirely if the bar
isn't cleared. Call report_digest with your result."""


def _internal_pattern_context(limit: int = 20) -> str:
    """Lane 2.1's internal-corroboration signal — a read-only cross-read of Knowledge Agent's
    promoted knowledge_base records across closed deals. Deliberately never writes back."""
    records = list_knowledge()
    if not records:
        return ""
    lines = [
        "\n\nINTERNAL PATTERNS FROM PAST CLOSED DEALS (read-only cross-read of Knowledge Agent's "
        "promoted knowledge_base — an internal-only pattern is a weaker signal than one also "
        "corroborated by external market commentary found via web_search):"
    ]
    for r in records[:limit]:
        lines.append(f"- [{r['category']}, {r['company_name']}] {r['summary'][:300]}")
    return "\n".join(lines)


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
                    "description": (
                        "Only include this if the proposal clears every bar in the meta-skill "
                        "checklist above — omit the whole object otherwise, don't fill it in "
                        "speculatively."
                    ),
                    "properties": {
                        "agent_name": {"type": "string", "enum": agent_names},
                        "specific_gap": {
                            "type": "string",
                            "description": "The concrete gap observed — what the agent would get wrong today, not a hypothetical",
                        },
                        "generality_check": {
                            "type": "string",
                            "description": "Why this generalizes beyond one deal, i.e. why it belongs in a platform-wide skill rather than per-deal precedent",
                        },
                        "additional_skill_instruction": {
                            "type": "string",
                            "description": "One or two sentences to ADD to this agent's skill.md, grounded specifically in what was just researched",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "The corroborating evidence — name more than one independent source",
                        },
                    },
                    "required": [
                        "agent_name",
                        "specific_gap",
                        "generality_check",
                        "additional_skill_instruction",
                        "rationale",
                    ],
                },
            },
            "required": ["digest"],
        },
    }


def run_learning_cycle(category: str, topic: str) -> dict[str, Any]:
    if category not in CATEGORY_TOPICS:
        raise ValueError(f"Invalid category: {category!r}")

    agent_names = [c["agent_name"] for c in list_agent_configs() if c["agent_name"] != "learning_agent"]
    internal_context = _internal_pattern_context() if category == "ma_training_data" else ""

    def _call() -> dict[str, Any]:
        response = call_model(
            "learning_agent",
            messages=[
                {
                    "role": "user",
                    "content": DIGEST_PROMPT.format(
                        topic_desc=CATEGORY_TOPICS[category], topic=topic, internal_context=internal_context
                    ),
                }
            ],
            tools=[WEB_SEARCH_TOOL, WEB_FETCH_TOOL, _digest_tool(agent_names)],
            betas=WEB_FETCH_BETAS,
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
        instruction = (
            f"{proposal['additional_skill_instruction']} "
            f"(gap: {proposal['specific_gap']} — generalizes because: {proposal['generality_check']} — "
            f"evidence: {proposal['rationale']})"
        )
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
