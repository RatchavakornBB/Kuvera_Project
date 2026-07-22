"""Real governance-loop wiring (system-architecture.md Section 11, ux-ui-spec.md Section 3.6) —
read by call_model() on every real LLM invocation, so an Admin-approved change to an agent's
model_id or skill_content takes effect on the next real call, no restart or redeploy.

get_agent_config() is on the hot path: call_model() invokes it on *every* LLM call, and a
multi-step agentic loop (agents/loop_runner.py) makes many calls per user message — each of
which was previously a fresh Supabase round-trip for a row that almost never changes mid-run.
A short per-process TTL cache collapses that to at most one lookup per agent per TTL window,
while a bounded TTL keeps an approved change live within TTL seconds even across processes.
The governance approval path (backend/app/services/governance.py) also calls
invalidate_agent_config_cache() on approve, so in the common single-process deployment an
approved change is still live on the very next call — the TTL is only the cross-process ceiling."""

import time
from typing import Any

from agents.db import get_client

# Short enough that a stale row can never outlive a single user turn by much, long
# enough that every call_model() in one agentic-loop run reuses one lookup. Governance
# approvals invalidate explicitly (see module docstring), so this is the cross-process
# staleness ceiling, not the typical case.
_CONFIG_CACHE_TTL_SECONDS = 10.0
_config_cache: dict[str, tuple[float, dict[str, Any] | None]] = {}


def invalidate_agent_config_cache(agent_name: str | None = None) -> None:
    """Drop the cached config for one agent (or all, if agent_name is None) so the
    next get_agent_config() re-reads from the DB. Called by the governance approval
    path the moment an agent's model_id/skill_content actually changes, so a change
    approved in this process is live on the very next call rather than up to
    _CONFIG_CACHE_TTL_SECONDS later."""
    if agent_name is None:
        _config_cache.clear()
    else:
        _config_cache.pop(agent_name, None)


def get_agent_config(agent_name: str) -> dict[str, Any] | None:
    now = time.monotonic()
    cached = _config_cache.get(agent_name)
    if cached is not None and now - cached[0] < _CONFIG_CACHE_TTL_SECONDS:
        return cached[1]
    client = get_client()
    res = client.table("agent_configs").select("*").eq("agent_name", agent_name).execute()
    value = res.data[0] if res.data else None
    _config_cache[agent_name] = (now, value)
    return value


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
