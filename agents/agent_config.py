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


def propose_skill_addition(agent_name: str, additional_instruction: str) -> dict[str, Any] | None:
    """Appends `additional_instruction` to `agent_name`'s current skill_content and
    files it as a real pending_changes row — the exact same governance queue a
    human editing the Skills tab uses (backend/app/services/governance.py's
    propose_change, duplicated minimally here rather than imported, since agents/
    stays independent of backend/ per D-007). Returns None if the agent doesn't
    exist (never silently no-ops on a typo)."""
    client = get_client()
    config = get_agent_config(agent_name)
    if config is None:
        return None

    old_value = config["skill_content"] or ""
    new_value = f"{old_value}\n{additional_instruction}".strip() if old_value else additional_instruction

    res = (
        client.table("pending_changes")
        .insert(
            {
                "agent_name": agent_name,
                "change_type": "skill_content",
                "old_value": old_value,
                "new_value": new_value,
            }
        )
        .execute()
    )
    return res.data[0]
