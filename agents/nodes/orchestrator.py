"""Orchestrator — system-architecture.md Section 4.4. Minimal
conditional-edge router this week (Section 4.3): the routing decision
itself is an LLM call, choosing between Concierge Q&A, the Analyst Lead
subgraph, the Contracts Lead, the Drafting Lead
(agents/nodes/drafting_router.py), web research (Section 5.2/5.3), and
chat-driven stage updates (agents/nodes/stage_update.py). The full hybrid
hard-route/LLM-route split from Section 5 is design-only for this build —
every chat message goes through this one classifier; only the EDGAR
decision *within* web_research is itself hard-routed (see
agents/nodes/web_research.py).

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
                "enum": [
                    "concierge_qa",
                    "analyst_lead",
                    "contracts_lead",
                    "drafting_lead",
                    "web_research",
                    "update_stage",
                ],
                "description": (
                    "'analyst_lead' only if the user is explicitly asking to run or "
                    "re-run GENERAL document analysis — risk flags, IC memo, pricing "
                    "(e.g. 'analyze the latest document', 're-run the risk flags') — not "
                    "for a request specifically about a contract's clauses or terms, "
                    "which is 'contracts_lead' instead. "
                    "'contracts_lead' only if the user is explicitly asking to run or "
                    "re-run CONTRACT-specific analysis or clause extraction (e.g. "
                    "'summarize this contract', 'extract the clauses', 're-run clause "
                    "extraction', 'what are the termination terms' when asking to "
                    "(re-)analyze rather than recall something already known) — not for "
                    "a question merely asking what a clause already says, which "
                    "'concierge_qa' can answer from data already extracted. "
                    "'drafting_lead' if the user is asking to draft/generate/write an IC "
                    "memo, IC deck/presentation, cover email, or source-cited summary for "
                    "this deal (e.g. 'draft the IC memo', 'write a cover email', 'make "
                    "the deck', 'give me a source-cited summary'). "
                    "'web_research' if the user is asking about a public company, "
                    "market/industry information, or anything requiring current "
                    "external/web information rather than this deal's own records "
                    "(e.g. 'what's a comparable company trading at', 'look up their "
                    "10-K', 'any recent news on X'). "
                    "'update_stage' only if the user is explicitly asking to move/advance/"
                    "change this deal's pipeline stage (e.g. 'move this deal to Due "
                    "Diligence', 'we signed the NDA, advance the stage', 'push to the next "
                    "stage') — not for questions merely asking what the current stage is. "
                    "'concierge_qa' for everything else — status questions, 'what's "
                    "the risk on X', general questions about THIS deal's own data."
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

VALID_ROUTES = (
    "concierge_qa",
    "analyst_lead",
    "contracts_lead",
    "drafting_lead",
    "web_research",
    "update_stage",
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
            if route not in VALID_ROUTES:
                raise ValueError(f"tool_use returned an invalid route: {route!r}")
            return route
    raise ValueError(f"model did not call route (stop_reason={response.stop_reason!r})")


def classify_intent(message: str) -> str:
    return with_retry("orchestrator", lambda: _run_once(message))
