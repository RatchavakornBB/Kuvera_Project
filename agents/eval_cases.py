"""Admin-authored eval test cases (system-architecture.md Section 11's eval-gated approval
loop, extended per explicit request: agents/evals.py's EVAL_CASES ships the built-in, code-
reviewed fixtures; this is the DB-backed layer that lets an admin add more real test cases
through the Admin > Eval Cases tab without touching code. run_eval() merges both sources for
a given agent_name — an admin only ever supplies prompt + criteria; the tool schema (if that
agent needs one) is wired automatically from evals.py's AGENT_TOOLS, so no one has to hand-
author a tool_use JSON schema to add a real test."""

from typing import Any

from agents.db import get_client


def list_eval_cases(agent_name: str | None = None) -> list[dict[str, Any]]:
    client = get_client()
    query = client.table("eval_cases").select("*")
    if agent_name:
        query = query.eq("agent_name", agent_name)
    return query.order("created_at", desc=True).execute().data


def create_eval_case(
    agent_name: str,
    prompt: str,
    criteria: str,
    expected_tool_sequence: list[str] | None = None,
    trajectory_rubric: str | None = None,
    max_iterations: int | None = None,
) -> dict[str, Any]:
    agent_name = agent_name.strip()
    prompt = prompt.strip()
    criteria = criteria.strip()
    if not agent_name:
        raise ValueError("agent_name is required")
    if not prompt:
        raise ValueError("prompt is required")
    if not criteria:
        raise ValueError("criteria is required")

    row: dict[str, Any] = {"agent_name": agent_name, "prompt": prompt, "criteria": criteria}
    # Only set when provided — agents/evals.py's run_eval() treats a
    # trajectory case as opt-in per case (expected_tool_sequence or
    # trajectory_rubric present), so an ordinary case for a loop-enabled
    # agent (contracts_lead/ic_memo_drafter/pricing_advisor) still runs the
    # existing single-shot grading path unless one of these is explicitly set.
    if expected_tool_sequence is not None:
        row["expected_tool_sequence"] = expected_tool_sequence
    trajectory_rubric = trajectory_rubric.strip() if trajectory_rubric else None
    if trajectory_rubric:
        row["trajectory_rubric"] = trajectory_rubric
    if max_iterations is not None:
        row["max_iterations"] = max_iterations

    client = get_client()
    res = client.table("eval_cases").insert(row).execute()
    return res.data[0]


def delete_eval_case(case_id: str) -> None:
    client = get_client()
    client.table("eval_cases").delete().eq("id", case_id).execute()
