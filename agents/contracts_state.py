from typing import Any, TypedDict


class ContractsState(TypedDict, total=False):
    document_id: str
    deal_id: str | None
    messages: list[dict]  # full Anthropic message history for this loop run
    last_response: Any  # anthropic.types.Message from the most recent decide() call
    iteration: int
    step_count: int  # cumulative tool-call count across rounds, for ToolStep.index continuity
    steps: list[dict]  # in-memory trajectory (also durably logged via agents.invocation_steps)
    tool_failure_counts: dict[str, int]
    tripped_tools: list[str]
    executed_side_effects: dict[str, str]
    invocation_id: str | None
    summary: str
    clauses: list[dict]
    circuit_broken_tools: list[str]
