"""Admin & Skill Governance (system-architecture.md Section 11) — real-scoped per the user's
explicit request after this screen was originally logged design-only. Every approved change here
writes into `agent_configs`, which `agents/adapters/model_adapter.py`'s `call_model()` reads on
every real LLM invocation — this is not a decorative admin UI."""

from datetime import datetime, timezone
from typing import Any

from agents.evals import run_eval

from app.db import get_client

VALID_CHANGE_TYPES = ("model_id", "skill_content")


def list_agents() -> list[dict[str, Any]]:
    client = get_client()
    return client.table("agent_configs").select("*").order("agent_name").execute().data


def create_agent(agent_name: str, model_id: str, skill_content: str = "") -> dict[str, Any]:
    """Provisions a brand-new agent_configs row — the row call_model() looks up by
    agent_name once real node code for that agent starts calling it. Not itself a
    governed change (nothing existing behavior to diff against), so it writes
    directly rather than going through pending_changes; a subsequent skill edit on
    this new row goes through the normal propose/approve flow like any other agent."""
    agent_name = agent_name.strip()
    if not agent_name:
        raise ValueError("agent_name is required")
    if not model_id.strip():
        raise ValueError("model_id is required")

    client = get_client()
    existing = client.table("agent_configs").select("id").eq("agent_name", agent_name).execute().data
    if existing:
        raise ValueError(f"Agent {agent_name!r} already exists")

    res = (
        client.table("agent_configs")
        .insert({"agent_name": agent_name, "model_id": model_id, "skill_content": skill_content})
        .execute()
    )
    return res.data[0]


def propose_skill_addition(agent_name: str, additional_instruction: str) -> dict[str, Any]:
    """Appends `additional_instruction` to `agent_name`'s current skill_content and files it
    through the same propose_change queue as any other edit — the human-facing "pick an agent,
    add one instruction" counterpart to agents/agent_config.py's function of the same name
    that Learning Agent uses for its own proposals (duplicated per D-007: agents/ stays
    independent of backend/)."""
    if not additional_instruction.strip():
        raise ValueError("additional_instruction is required")

    client = get_client()
    config_rows = client.table("agent_configs").select("*").eq("agent_name", agent_name).execute().data
    if not config_rows:
        raise ValueError(f"Unknown agent: {agent_name!r}")

    old_value = config_rows[0]["skill_content"] or ""
    new_value = f"{old_value}\n{additional_instruction}".strip() if old_value else additional_instruction.strip()
    return propose_change(agent_name, "skill_content", new_value)


def propose_change(agent_name: str, change_type: str, new_value: str) -> dict[str, Any]:
    if change_type not in VALID_CHANGE_TYPES:
        raise ValueError(f"Invalid change_type: {change_type!r}")

    client = get_client()
    config_rows = client.table("agent_configs").select("*").eq("agent_name", agent_name).execute().data
    if not config_rows:
        raise ValueError(f"Unknown agent: {agent_name!r}")

    old_value = config_rows[0][change_type]
    res = (
        client.table("pending_changes")
        .insert(
            {
                "agent_name": agent_name,
                "change_type": change_type,
                "old_value": old_value,
                "new_value": new_value,
            }
        )
        .execute()
    )
    return res.data[0]


def list_pending_changes(status: str = "pending") -> list[dict[str, Any]]:
    client = get_client()
    return (
        client.table("pending_changes")
        .select("*")
        .eq("status", status)
        .order("proposed_at", desc=True)
        .execute()
        .data
    )


def _resolve_change(change_id: str, action: str) -> dict[str, Any]:
    client = get_client()
    rows = client.table("pending_changes").select("*").eq("id", change_id).execute().data
    if not rows:
        raise ValueError(f"No pending change with id {change_id}")
    change = rows[0]
    if change["status"] != "pending":
        raise ValueError(f"Change {change_id} is already {change['status']}")

    now = datetime.now(timezone.utc).isoformat()

    if action == "approved":
        client.table("agent_configs").update(
            {change["change_type"]: change["new_value"], "updated_at": now}
        ).eq("agent_name", change["agent_name"]).execute()

    client.table("pending_changes").update({"status": action, "reviewed_at": now}).eq("id", change_id).execute()

    client.table("audit_log").insert(
        {
            "agent_name": change["agent_name"],
            "change_type": change["change_type"],
            "old_value": change["old_value"],
            "new_value": change["new_value"],
            "action": action,
        }
    ).execute()

    return {**change, "status": action, "reviewed_at": now}


def approve_change(change_id: str) -> dict[str, Any]:
    return _resolve_change(change_id, "approved")


def reject_change(change_id: str) -> dict[str, Any]:
    return _resolve_change(change_id, "rejected")


def list_audit_log() -> list[dict[str, Any]]:
    client = get_client()
    return client.table("audit_log").select("*").order("created_at", desc=True).execute().data


def run_eval_for_change(change_id: str) -> dict[str, Any]:
    client = get_client()
    rows = client.table("pending_changes").select("*").eq("id", change_id).execute().data
    if not rows:
        raise ValueError(f"No pending change with id {change_id}")
    change = rows[0]

    config_rows = client.table("agent_configs").select("*").eq("agent_name", change["agent_name"]).execute().data
    current_config = config_rows[0] if config_rows else {"model_id": "claude-sonnet-5", "skill_content": ""}

    if change["change_type"] == "skill_content":
        skill_content = change["new_value"]
        model_id = current_config["model_id"]
    else:
        skill_content = current_config["skill_content"] or ""
        model_id = change["new_value"]

    result = run_eval(change["agent_name"], skill_content, model_id)

    client.table("pending_changes").update(
        {"eval_pass_rate": result["pass_rate"], "eval_results": result["results"]}
    ).eq("id", change_id).execute()

    return result
