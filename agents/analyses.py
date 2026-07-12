"""Analyst Lead run history (public.analyses) — read/write helpers for the
"last stored version" the lightweight contradiction check compares against
(timeline Section 6 Phase 2 / system-architecture.md Section 10.5, scoped
down: a visible flag, no confidence scoring)."""

from typing import Any

from agents.db import get_client


def get_last_analysis(deal_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = (
        client.table("analyses")
        .select("*")
        .eq("deal_id", deal_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def save_analysis(
    deal_id: str,
    document_id: str,
    summary: str,
    risk_flags: list[dict],
    ic_memo_draft: str | None = None,
    pricing_note: str | None = None,
) -> dict[str, Any]:
    client = get_client()
    res = (
        client.table("analyses")
        .insert(
            {
                "deal_id": deal_id,
                "document_id": document_id,
                "summary": summary,
                "risk_flags": risk_flags,
                "ic_memo_draft": ic_memo_draft,
                "pricing_note": pricing_note,
            }
        )
        .execute()
    )
    return res.data[0]
