"""Admin & Skill Governance (system-architecture.md Section 11) — real-scoped per the user's
explicit request after this screen was originally logged design-only. Every approved change here
writes into `agent_configs`, which `agents/adapters/model_adapter.py`'s `call_model()` reads on
every real LLM invocation — this is not a decorative admin UI."""

from datetime import datetime, timezone
from typing import Any

from app.db import get_client

VALID_CHANGE_TYPES = ("model_id", "skill_content")


def list_agents() -> list[dict[str, Any]]:
    client = get_client()
    return client.table("agent_configs").select("*").order("agent_name").execute().data


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
