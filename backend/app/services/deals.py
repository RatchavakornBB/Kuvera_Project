"""The one write/read path for the deals resource — routes call these
functions, never the supabase client directly."""

import sys
import threading
import traceback
from datetime import datetime, timezone
from typing import Any

from agents.knowledge import promote_deal_to_knowledge

from app.db import get_client

_DEAL_SELECT = "*, owner:users(id, full_name, initials)"

STAGES = (
    "Lead",
    "NDA",
    "Sourcing & Screening",
    "Valuation & Bidding",
    "Strategy & Preparation",
    "Due Diligence",
    "Negotiation & Closing",
)


def _seed_stage_phases(deal_id: str) -> None:
    """Give a freshly created deal the 7 pipeline stages as default plan phases
    (source='stage'). Mirrors the backfill in migration 20260722160000 so every
    deal — old or new — opens the Project Plan tab with the same starting phases."""
    client = get_client()
    rows = [
        {"deal_id": deal_id, "name": name, "sort_order": i, "source": "stage"}
        for i, name in enumerate(STAGES)
    ]
    client.table("deal_phases").insert(rows).execute()


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
    deal = res.data[0]
    _seed_stage_phases(deal["id"])
    _draft_nda_async(deal["id"])
    return deal


def _draft_nda_async(deal_id: str) -> None:
    """After a deal is created, the Drafting Lead auto-drafts a mutual NDA and
    drops it into the deal's Documents tab. Runs on a daemon thread and is
    best-effort: an NDA-draft failure (LLM error/timeout/embeddings) must never
    make deal creation fail or hang — the deal row is already committed. Mirrors
    the background best-effort pattern used for citation-link fetching in
    app/services/documents.py. The underlying call_model() invocation is logged
    to agent_invocations regardless, and any post-model failure is printed to
    stderr rather than swallowed silently, so a demo failure is diagnosable."""

    def _run() -> None:
        try:
            from agents.drafting_lead import draft_and_store_nda

            draft_and_store_nda(deal_id)
        except Exception as e:  # noqa: BLE001 — background best-effort, must not propagate
            print(f"[nda-draft] failed for deal {deal_id}: {e}", file=sys.stderr)
            traceback.print_exc()

    threading.Thread(target=_run, daemon=True).start()


def update_deal_stage(deal_id: str, stage: str) -> dict[str, Any] | None:
    """The single write path for stage changes — used by the manual UI
    control, the chat agent's stage_update tool, and (for the 'Stalled'
    status only, never 'stage' itself) the scheduler's stalled-deal check.
    Resets stage_entered_at and clears a stale 'Stalled' status, since
    moving stages is itself evidence the deal isn't stalled anymore."""
    if stage not in STAGES:
        raise ValueError(f"Invalid stage: {stage!r}")
    client = get_client()
    fields: dict[str, Any] = {"stage": stage, "stage_entered_at": datetime.now(timezone.utc).isoformat()}
    deal = client.table("deals").select("status").eq("id", deal_id).execute().data
    if deal and deal[0]["status"] == "Stalled":
        fields["status"] = "On track"
    res = client.table("deals").update(fields).eq("id", deal_id).execute()
    return res.data[0] if res.data else None


def create_task(
    deal_id: str,
    text: str,
    owner_id: str | None,
    due_date: str | None,
    phase_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    client = get_client()
    res = (
        client.table("tasks")
        .insert(
            {
                "deal_id": deal_id,
                "text": text,
                "owner_id": owner_id,
                "due_date": due_date,
                "phase_id": phase_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        .execute()
    )
    return res.data[0]


def update_task(deal_id: str, task_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
    client = get_client()
    res = client.table("tasks").update(fields).eq("id", task_id).eq("deal_id", deal_id).execute()
    return res.data[0] if res.data else None


# --- Project-plan phases (Gantt) -------------------------------------------


def create_phase(deal_id: str, name: str, sort_order: int | None = None, color: str | None = None) -> dict[str, Any]:
    """Adds a custom phase. If no sort_order is given, it lands after the last
    existing phase so new phases append to the bottom of the timeline."""
    client = get_client()
    if sort_order is None:
        existing = client.table("deal_phases").select("sort_order").eq("deal_id", deal_id).execute().data
        sort_order = (max((p["sort_order"] for p in existing), default=-1)) + 1
    res = (
        client.table("deal_phases")
        .insert({"deal_id": deal_id, "name": name, "sort_order": sort_order, "color": color, "source": "custom"})
        .execute()
    )
    return res.data[0]


def update_phase(deal_id: str, phase_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
    client = get_client()
    res = client.table("deal_phases").update(fields).eq("id", phase_id).eq("deal_id", deal_id).execute()
    return res.data[0] if res.data else None


def delete_phase(deal_id: str, phase_id: str) -> bool:
    """Deletes a phase. Its tasks survive with phase_id set null (the FK is
    ON DELETE SET NULL), landing in the unscheduled tray rather than vanishing."""
    client = get_client()
    res = client.table("deal_phases").delete().eq("id", phase_id).eq("deal_id", deal_id).execute()
    return bool(res.data)


def close_deal(deal_id: str, outcome: str) -> dict[str, Any]:
    """Real promotion trigger for the Knowledge Agent (system-architecture.md
    Section 10.1's "on deal close"). Sets the deal Closed and synthesizes
    real knowledge_base records from that deal's actual data — not a stub."""
    client = get_client()
    client.table("deals").update({"status": "Closed"}).eq("id", deal_id).execute()
    records = promote_deal_to_knowledge(deal_id, outcome)
    return {"deal_id": deal_id, "outcome": outcome, "knowledge_records_created": len(records)}


def flag_stalled_deals(stalled_after_days: int = 14) -> list[dict[str, Any]]:
    """Scheduler-only: flags status='Stalled' for open deals that have sat
    in the same stage too long. Never touches `stage` itself — advancing
    a deal is a judgment call for a person or an explicit chat instruction,
    not something a timer should decide (system-architecture.md 3.2's
    "surfaces stalled deals automatically" is a flag, not an auto-advance)."""
    client = get_client()
    cutoff = datetime.now(timezone.utc).timestamp() - stalled_after_days * 86400
    cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()

    candidates = (
        client.table("deals")
        .select("id, name, stage, stage_entered_at, status")
        .neq("status", "Closed")
        .neq("status", "Stalled")
        .lt("stage_entered_at", cutoff_iso)
        .execute()
        .data
    )
    for deal in candidates:
        client.table("deals").update({"status": "Stalled"}).eq("id", deal["id"]).execute()
    return candidates


def get_deal(deal_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = client.table("deals").select(_DEAL_SELECT).eq("id", deal_id).execute()
    if not res.data:
        return None
    deal = res.data[0]

    deal["contacts"] = client.table("contacts").select("*").eq("deal_id", deal_id).execute().data
    deal["documents"] = client.table("documents").select("*").eq("deal_id", deal_id).execute().data
    deal["tasks"] = client.table("tasks").select("*").eq("deal_id", deal_id).execute().data
    deal["phases"] = (
        client.table("deal_phases").select("*").eq("deal_id", deal_id).order("sort_order").execute().data
    )
    deal["meeting_notes"] = client.table("meeting_notes").select("*").eq("deal_id", deal_id).execute().data
    deal["dd_items"] = client.table("dd_items").select("*").eq("deal_id", deal_id).execute().data
    deal["milestones"] = (
        client.table("milestones").select("*").eq("deal_id", deal_id).order("sort_order").execute().data
    )
    return deal
