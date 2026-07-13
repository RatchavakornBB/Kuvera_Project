"""Real governance-loop wiring (system-architecture.md Section 11, ux-ui-spec.md Section 3.6) —
read by call_model() on every real LLM invocation, so an Admin-approved change to an agent's
model_id or skill_content takes effect on the very next real call, no restart or redeploy."""

from typing import Any

from agents.db import get_client


def get_agent_config(agent_name: str) -> dict[str, Any] | None:
    client = get_client()
    res = client.table("agent_configs").select("*").eq("agent_name", agent_name).execute()
    return res.data[0] if res.data else None


def list_agent_configs() -> list[dict[str, Any]]:
    client = get_client()
    return client.table("agent_configs").select("*").order("agent_name").execute().data
