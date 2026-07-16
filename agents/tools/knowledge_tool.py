"""Anthropic tool-schema wrapper around agents.knowledge.search_knowledge().

Before this file, search_knowledge() was only ever called directly from Python
(historical_precedent_context, a forced pre-fetch stuffed into a prompt as
static context) — never something the model could invoke mid-turn. This is the
first tool a loop-enabled agent (agents/loop_runner.py) can call on demand:
Contracts Lead, IC memo drafter, and pricing advisor all import the same
SEARCH_KNOWLEDGE_SPEC instance, unmodified, rather than each defining their own
copy of the schema."""

import json

from agents.knowledge import search_knowledge
from agents.loop_runner import ToolSpec

SEARCH_KNOWLEDGE_TOOL = {
    "name": "search_knowledge",
    "description": (
        "Search Kuvera's knowledge base of past closed deals for precedent — pricing, "
        "clauses, risk outcomes, and evaluation approach. Call this when comparable-deal "
        "context would ground your analysis; do not call it speculatively, and do not call "
        "it more than a couple of times per task."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query_text": {"type": "string", "description": "What to search for, in plain language."},
            "industry": {"type": "string", "description": "Optional industry filter."},
            "category": {
                "type": "string",
                "description": (
                    "Optional knowledge_base category filter, e.g. 'deal_profile', "
                    "'risk_signals_resolution', 'industry_insight'."
                ),
            },
            "limit": {"type": "integer", "description": "Max results, default 5."},
        },
        "required": ["query_text"],
    },
}


def dispatch_search_knowledge(tool_input: dict) -> str:
    results = search_knowledge(
        tool_input["query_text"],
        industry=tool_input.get("industry"),
        category=tool_input.get("category"),
        limit=tool_input.get("limit", 5),
    )
    if not results:
        return "No matching knowledge base entries found."
    return json.dumps(results, default=str)


SEARCH_KNOWLEDGE_SPEC = ToolSpec(schema=SEARCH_KNOWLEDGE_TOOL, handler=dispatch_search_knowledge, idempotent=True)
