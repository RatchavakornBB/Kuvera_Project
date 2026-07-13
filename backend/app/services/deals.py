"""The one write/read path for the deals resource — routes call these
functions, never the supabase client directly."""

from typing import Any

from app.db import get_client

_DEAL_SELECT = "*, owner:users(id, full_name, initials)"


def _doc_pending_count(deal_id: str) -> int:
    client = get_client()
    res = (
        client.table("documents")
        .select("id", count="exact")
        .eq("deal_id", deal_id)
        .in_("status", ["requested", "received", "pending", "under_review"])
        .execute()
    )
    return res.count or 0


def _latest_risk_flag_count(deal_id: str) -> int:
    # Real risk_flagger output now exists (Phase 2) — this was hardcoded to
    # 0 in phase1-006 before the Analyst Lead was built; completing it now
    # that the blocker is resolved, not a gratuitous change.
    client = get_client()
    res = (
        client.table("analyses")
        .select("risk_flags")
        .eq("deal_id", deal_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return 0
    return len(res.data[0]["risk_flags"] or [])


def list_deals(
    stage: str | None = None,
    industry: str | None = None,
    owner: str | None = None,
) -> list[dict[str, Any]]:
    client = get_client()
    query = client.table("deals").select(_DEAL_SELECT)
    if stage:
        query = query.eq("stage", stage)
    if owner:
        query = query.eq("owner_id", owner)
    if industry:
        query = query.contains("industries", [industry])
    deals = query.order("created_at").execute().data

    for deal in deals:
        deal["docs_pending"] = _doc_pending_count(deal["id"])
        deal["risk_flags"] = _latest_risk_flag_count(deal["id"])

    return deals


def create_deal(name: str, client_name: str, industries: list[str], owner_id: str | None) -> dict[str, Any]:
    client = get_client()
    res = (
        client.table("deals")
        .insert(
            {
                "name": name,
                "client": client_name,
                "industries": industries,
                "stage": "Lead",
                "owner_id": owner_id,
            }
        )
        .execute()
    )
    return res.data[0]


def get_deal(deal_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = client.table("deals").select(_DEAL_SELECT).eq("id", deal_id).execute()
    if not res.data:
        return None
    deal = res.data[0]

    deal["contacts"] = client.table("contacts").select("*").eq("deal_id", deal_id).execute().data
    deal["documents"] = client.table("documents").select("*").eq("deal_id", deal_id).execute().data
    deal["tasks"] = client.table("tasks").select("*").eq("deal_id", deal_id).execute().data
    deal["meeting_notes"] = client.table("meeting_notes").select("*").eq("deal_id", deal_id).execute().data
    deal["dd_items"] = client.table("dd_items").select("*").eq("deal_id", deal_id).execute().data
    deal["milestones"] = (
        client.table("milestones").select("*").eq("deal_id", deal_id).order("sort_order").execute().data
    )
    return deal
