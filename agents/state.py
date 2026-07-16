from typing import Any, TypedDict


class RiskFlag(TypedDict):
    severity: str
    description: str
    source_excerpt: str


class AnalystState(TypedDict, total=False):
    deal_id: str
    document_id: str
    summary: str
    risk_flags: list[RiskFlag]
    ic_memo_draft: str
    pricing_note: str | None
    pricing_error: dict  # set only if pricing_advisor degraded gracefully (AGENT.md Section 10)

    # ic_memo_drafter and pricing_advisor both run in PARALLEL via the existing
    # Send() fan-out (agents/graph.py) and are each now a decide<->act<->finalize
    # agentic loop (agents/loop_runner.py) — every working field below is
    # namespace-prefixed per sub-loop so LangGraph's merge of the two parallel
    # branches' partial state updates never collides, same disjoint-key
    # convention already used for ic_memo_draft vs pricing_note/pricing_error.
    ic_memo_messages: list[dict]
    ic_memo_last_response: Any
    ic_memo_iteration: int
    ic_memo_step_count: int
    ic_memo_steps: list[dict]
    ic_memo_tool_failures: dict[str, int]
    ic_memo_tripped_tools: list[str]
    ic_memo_executed_side_effects: dict[str, str]
    ic_memo_invocation_id: str | None

    pricing_messages: list[dict]
    pricing_last_response: Any
    pricing_iteration: int
    pricing_step_count: int
    pricing_steps: list[dict]
    pricing_tool_failures: dict[str, int]
    pricing_tripped_tools: list[str]
    pricing_executed_side_effects: dict[str, str]
    pricing_invocation_id: str | None
