"""Orchestrator — system-architecture.md Section 4.4. Minimal
conditional-edge router this week (Section 4.3): the routing decision
itself is an LLM call, choosing between Concierge Q&A and the Analyst
Lead subgraph. The full hybrid hard-route/LLM-route split from Section 5
is design-only for this build — every chat message goes through this one
classifier.

deal_id is required for either route (AGENT.md Section 11 invariant,
extended to chat): with no deal context, the Orchestrator asks which deal
rather than guessing or answering across deals.
"""

from agents.adapters.model_adapter import call_model
from agents.retry import with_retry

ROUTE_TOOL = {
    "name": "route",
    "description": "Decide which Lead should handle this chat message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "route": {
                "type": "string",
                "enum": ["concierge_qa", "analyst_lead"],
                "description": (
                    "'analyst_lead' only if the user is explicitly asking to run or "
                    "re-run document analysis (e.g. 'analyze the latest document', "
                    "'summarize this contract', 're-run the risk flags'). "
                    "'concierge_qa' for everything else — status questions, 'what's "
                    "the risk on X', general questions about the deal."
                ),
            }
        },
        "required": ["route"],
    },
}

CLASSIFY_PROMPT = (
    "Classify this chat message about a specific deal. Call route with your decision.\n\n"
    "MESSAGE: {message}"
)


def _run_once(message: str) -> str:
    response = call_model(
        "orchestrator",
        messages=[{"role": "user", "content": CLASSIFY_PROMPT.format(message=message)}],
        tools=[ROUTE_TOOL],
        max_tokens=256,
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "route":
            route = block.input.get("route")
            if route not in ("concierge_qa", "analyst_lead"):
                raise ValueError(f"tool_use returned an invalid route: {route!r}")
            return route
    raise ValueError(f"model did not call route (stop_reason={response.stop_reason!r})")


def classify_intent(message: str) -> str:
    return with_retry("orchestrator", lambda: _run_once(message))
