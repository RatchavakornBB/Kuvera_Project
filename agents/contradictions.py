"""Full Contradiction & Hypothesis confidence-scoring engine — extends the lightweight
contradiction check already live in risk_flagger.py (a plain risk flag) with real structured
tracking: status ranks, corroboration counting via real pgvector similarity (the description text
is freshly LLM-generated on every re-analysis, never identical to a prior run's wording, so exact
matching isn't viable), and versioned promotion into the Knowledge Agent once resolved."""

from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

from agents.config import settings
from agents.db import get_client
from agents.embeddings import embed_text

# Calibrated against real Voyage embeddings, not guessed: a genuine paraphrase
# of the same contradiction scored 0.77 cosine similarity in testing, while an
# unrelated contradiction scored 0.50 — 0.70 sits with real margin on both sides.
SIMILARITY_THRESHOLD = 0.70


def record_contradiction(deal_id: str, description: str, source_excerpt: str) -> dict[str, Any]:
    """Called from risk_flagger when the model flags a contradiction. Finds the
    most similar open (non-refuted) contradiction for this deal via cosine
    similarity; if it's the same one recurring, increments corroboration
    instead of duplicating a row."""
    embedding = embed_text(description, input_type="document")
    embedding_literal = "[" + ",".join(str(x) for x in embedding) + "]"

    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(
            """
            select id, corroboration_count, status,
                   1 - (embedding <=> %s::vector) as similarity
            from contradictions
            where deal_id = %s and status != 'refuted' and embedding is not null
            order by embedding <=> %s::vector
            limit 1
            """,
            [embedding_literal, deal_id, embedding_literal],
        )
        existing = cur.fetchone()

    client = get_client()
    now = datetime.now(timezone.utc).isoformat()

    if existing and existing["similarity"] >= SIMILARITY_THRESHOLD:
        new_count = existing["corroboration_count"] + 1
        new_status = existing["status"]
        if new_status == "unconfirmed" and new_count >= 2:
            new_status = "corroborated"
        client.table("contradictions").update(
            {"corroboration_count": new_count, "status": new_status, "last_seen_at": now}
        ).eq("id", existing["id"]).execute()
        return {"id": existing["id"], "status": new_status, "corroboration_count": new_count, "matched_prior": True}

    res = (
        client.table("contradictions")
        .insert(
            {
                "deal_id": deal_id,
                "description": description,
                "source_excerpt": source_excerpt,
                "embedding": embedding,
            }
        )
        .execute()
    )
    row = res.data[0]
    return {"id": row["id"], "status": row["status"], "corroboration_count": row["corroboration_count"], "matched_prior": False}


def list_contradictions(deal_id: str) -> list[dict[str, Any]]:
    client = get_client()
    return (
        client.table("contradictions")
        .select("id, deal_id, description, source_excerpt, status, corroboration_count, first_flagged_at, last_seen_at, resolved_at, resolution_note, promoted_to_knowledge_base")
        .eq("deal_id", deal_id)
        .order("last_seen_at", desc=True)
        .execute()
        .data
    )


def resolve_contradiction(contradiction_id: str, resolution: str, resolution_note: str) -> dict[str, Any]:
    """resolution: 'resolved' (the contradiction was real and has been addressed)
    or 'refuted' (it was a false positive / doesn't apply). Resolving promotes a
    versioned record into the Knowledge Agent's knowledge_base — the "versioned
    promotion" half of this feature's one-line spec."""
    if resolution not in ("resolved", "refuted"):
        raise ValueError(f"resolution must be 'resolved' or 'refuted', got {resolution!r}")

    client = get_client()
    rows = client.table("contradictions").select("*").eq("id", contradiction_id).execute().data
    if not rows:
        raise ValueError(f"No contradiction with id {contradiction_id}")
    contradiction = rows[0]

    now = datetime.now(timezone.utc).isoformat()
    client.table("contradictions").update(
        {"status": resolution, "resolved_at": now, "resolution_note": resolution_note}
    ).eq("id", contradiction_id).execute()

    if resolution == "resolved":
        _promote_to_knowledge_base(contradiction, resolution_note)
        client.table("contradictions").update({"promoted_to_knowledge_base": True}).eq("id", contradiction_id).execute()

    return {"id": contradiction_id, "status": resolution}


def _promote_to_knowledge_base(contradiction: dict[str, Any], resolution_note: str) -> None:
    client = get_client()
    deal_rows = client.table("deals").select("name, industries").eq("id", contradiction["deal_id"]).execute().data
    deal = deal_rows[0] if deal_rows else {}

    content = {
        "contradiction": contradiction["description"],
        "source_excerpt": contradiction.get("source_excerpt"),
        "corroboration_count": contradiction["corroboration_count"],
        "resolution": resolution_note,
        "materialized": "yes",
        "version": contradiction["corroboration_count"],
    }
    summary = (
        f"[risk_signals_resolution]\ncontradiction: {contradiction['description']}\n"
        f"resolution: {resolution_note}\ncorroborated {contradiction['corroboration_count']} time(s)"
    )
    embedding = embed_text(summary, input_type="document")

    client.table("knowledge_base").insert(
        {
            "source_deal_id": contradiction["deal_id"],
            "category": "risk_signals_resolution",
            "company_name": deal.get("name"),
            "industry": (deal.get("industries") or [None])[0],
            "content": content,
            "summary": summary,
            "embedding": embedding,
        }
    ).execute()
