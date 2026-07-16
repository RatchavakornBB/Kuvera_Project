"""Per-tool-call step logging for multi-step agentic loops (agents/loop_runner.py).
Mirrors agents/activity_tracker.py's swallow-on-failure pattern exactly — logging a
step must never break a real agent run over a tracking-table hiccup. One row per
tool call, scoped to the invocation_id an agents.activity_tracker.start_invocation()
call already returned for the whole run."""

import json
from typing import Any

from agents.db import get_client


def log_step(
    invocation_id: str | None,
    step_index: int,
    tool_name: str,
    tool_input: dict,
    tool_output: str | None,
    status: str,
) -> None:
    if invocation_id is None:
        return
    try:
        client = get_client()
        client.table("agent_invocation_steps").insert(
            {
                "invocation_id": invocation_id,
                "step_index": step_index,
                "tool_name": tool_name,
                "tool_input": json.loads(json.dumps(tool_input, default=str)),
                "tool_output": tool_output,
                "status": status,
            }
        ).execute()
    except Exception:
        pass


def list_steps(invocation_id: str) -> list[dict[str, Any]]:
    client = get_client()
    return (
        client.table("agent_invocation_steps")
        .select("*")
        .eq("invocation_id", invocation_id)
        .order("step_index")
        .execute()
        .data
    )
