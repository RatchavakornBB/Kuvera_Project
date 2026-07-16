from typing import Any

from agents.activity_log import list_activity
from agents.activity_tracker import current_status, recent_invocations, sparkline_7day
from agents.agent_config import list_agent_configs

from app.db import get_client

# Which Lead each real agent belongs to — architectural grouping metadata,
# not stored data (system-architecture.md's Lead structure). Keep in sync
# with agent_configs: a new agent with no entry here just falls into
# "Ungrouped" rather than crashing the grid.
LEAD_GROUPS: dict[str, str] = {
    "doc_summarizer": "Analyst Lead",
    "risk_flagger": "Analyst Lead",
    "ic_memo_drafter": "Analyst Lead",
    "pricing_advisor": "Analyst Lead",
    "contract_summarizer": "Contracts Lead",  # superseded by contracts_lead's agentic loop; kept for eval fixtures
    "clause_extractor": "Contracts Lead",  # superseded by contracts_lead's agentic loop; kept for eval fixtures
    "contracts_lead": "Contracts Lead",
    "concierge_qa": "Concierge",
    "orchestrator": "Orchestrator",
    "knowledge_promoter": "Knowledge Agent",
    "industry_brief": "Knowledge Agent",
    "competitor_brief": "Knowledge Agent",
    "company_research": "Knowledge Agent",
    "learning_agent": "Learning Agent",
    "drafting_lead": "Drafting Lead",
}

# The Analyst Lead's real, actual LangGraph edges (agents/graph.py) — used
# for the live graph view. Any change to that graph's shape must be mirrored
# here, or the "live" view stops matching the real orchestration.
#
# ic_memo_drafter and pricing_advisor are each internally three LangGraph
# nodes now (decide/act/finalize, agents/nodes/ic_memo_drafter.py /
# pricing_advisor.py) — but every internal node still calls
# call_model_step() under the single "ic_memo_drafter"/"pricing_advisor"
# agent_name, so status tracking (agent_invocations, keyed by agent_name)
# is unaffected. This view keeps those two as one conceptual node each, with
# a self-loop edge added to represent the real decide<->act cycle honestly,
# rather than fragmenting the grid's live-status lookup across sub-node
# names that don't correspond to any real agent_configs row.
ANALYST_LEAD_GRAPH = {
    "nodes": ["doc_summarizer", "risk_flagger", "ic_memo_drafter", "pricing_advisor"],
    "edges": [
        {"from": "doc_summarizer", "to": "risk_flagger"},
        {"from": "risk_flagger", "to": "ic_memo_drafter"},
        {"from": "risk_flagger", "to": "pricing_advisor"},
        {"from": "ic_memo_drafter", "to": "ic_memo_drafter"},
        {"from": "pricing_advisor", "to": "pricing_advisor"},
    ],
}


def get_activity(limit: int = 50) -> list[dict[str, Any]]:
    events = list_activity(limit=limit)
    if not events:
        return events

    client = get_client()

    deal_ids = {e["deal_id"] for e in events if e["deal_id"]}
    deal_names: dict[str, str] = {}
    if deal_ids:
        deals = client.table("deals").select("id, name").in_("id", list(deal_ids)).execute().data
        deal_names = {d["id"]: d["name"] for d in deals}

    document_ids = {e["document_id"] for e in events if e["document_id"]}
    document_names: dict[str, str] = {}
    if document_ids:
        documents = client.table("documents").select("id, name").in_("id", list(document_ids)).execute().data
        document_names = {d["id"]: d["name"] for d in documents}

    for event in events:
        event["deal_name"] = deal_names.get(event["deal_id"])
        event["document_name"] = document_names.get(event["document_id"])

    return events


def get_agent_grid() -> list[dict[str, Any]]:
    configs = list_agent_configs()
    statuses = {s["agent_name"]: s for s in current_status()}

    grid = []
    for config in configs:
        name = config["agent_name"]
        status_row = statuses.get(name)
        if status_row is None:
            live_status = "idle"
            last_active = None
        elif status_row["status"] == "running":
            live_status = "active"
            last_active = status_row["started_at"]
        elif status_row["status"] == "error":
            live_status = "error"
            last_active = status_row["completed_at"] or status_row["started_at"]
        else:
            live_status = "idle"
            last_active = status_row["completed_at"] or status_row["started_at"]

        grid.append(
            {
                "agent_name": name,
                "lead": LEAD_GROUPS.get(name, "Ungrouped"),
                "model_id": config["model_id"],
                "has_skill": bool(config["skill_content"]),
                "status": live_status,
                "last_active": last_active,
                "error_reason": status_row["error_reason"] if status_row and status_row["status"] == "error" else None,
            }
        )
    return grid


def get_agent_detail(agent_name: str) -> dict[str, Any]:
    return {
        "agent_name": agent_name,
        "lead": LEAD_GROUPS.get(agent_name, "Ungrouped"),
        "recent_invocations": recent_invocations(agent_name, limit=20),
        "sparkline_7day": sparkline_7day(agent_name),
    }


def get_analyst_lead_graph() -> dict[str, Any]:
    grid = {row["agent_name"]: row for row in get_agent_grid()}
    nodes = [
        {"name": n, "status": grid[n]["status"] if n in grid else "idle"} for n in ANALYST_LEAD_GRAPH["nodes"]
    ]
    return {"nodes": nodes, "edges": ANALYST_LEAD_GRAPH["edges"]}
