"""Real, uniform activity tracking for every agent — read by the Agent Hub's grid/live-graph view
(ux-ui-spec.md Section 3.5). Called from call_model(), the one real chokepoint every agent already
goes through, so this covers all of them uniformly rather than only the 4 Analyst Lead nodes the
older checkpoint-based log (agents/activity_log.py) can see. Logging failures are swallowed — this
is observability, not a required part of any agent's real output, and must never break a real LLM
call over a tracking-table hiccup."""

from datetime import datetime, timezone
from typing import Any

from agents.db import get_client


def start_invocation(agent_name: str) -> str | None:
    try:
        client = get_client()
        res = client.table("agent_invocations").insert({"agent_name": agent_name, "status": "running"}).execute()
        return res.data[0]["id"]
    except Exception:
        return None


def finish_invocation(invocation_id: str | None, status: str, error_reason: str | None = None) -> None:
    if invocation_id is None:
        return
    try:
        client = get_client()
        client.table("agent_invocations").update(
            {"status": status, "error_reason": error_reason, "completed_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", invocation_id).execute()
    except Exception:
        pass


def current_status() -> list[dict[str, Any]]:
    """Most recent invocation per agent — the live status dot's data source."""
    client = get_client()
    rows = (
        client.table("agent_invocations")
        .select("agent_name, status, error_reason, started_at, completed_at")
        .order("started_at", desc=True)
        .limit(500)
        .execute()
        .data
    )
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["agent_name"] not in latest:
            latest[row["agent_name"]] = row
    return list(latest.values())


def recent_invocations(agent_name: str, limit: int = 20) -> list[dict[str, Any]]:
    client = get_client()
    return (
        client.table("agent_invocations")
        .select("*")
        .eq("agent_name", agent_name)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )


def sparkline_7day(agent_name: str) -> list[int]:
    """Real per-day invocation counts for the last 7 days (today last).
    Only reflects activity since this table started recording — honest, not
    backfilled with fabricated history."""
    client = get_client()
    rows = (
        client.table("agent_invocations")
        .select("started_at")
        .eq("agent_name", agent_name)
        .execute()
        .data
    )
    today = datetime.now(timezone.utc).date()
    counts = [0] * 7
    for row in rows:
        day = datetime.fromisoformat(row["started_at"]).date()
        offset = (today - day).days
        if 0 <= offset < 7:
            counts[6 - offset] += 1
    return counts
