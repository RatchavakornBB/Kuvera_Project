"""Agent Hub activity log — 5day-build-timeline.md's scoped-down Phase 4 slot:
"a static activity log table (which node ran, when, success/fail) reading
from LangGraph Checkpointer state — not the full live graph view." Reads the
real Postgres Checkpointer tables the Analyst Lead graph already writes to
(agents/graph.py) rather than a separate audit log, so this can never drift
from what actually executed."""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from agents.config import settings

# AnalystState field -> the node that owns writing it (agents/state.py).
# pricing_note is written by pricing_advisor even on its own degraded-failure
# path (it swallows NodeFailure and returns pricing_note=None + pricing_error
# instead of raising), so this mapping alone is enough to attribute every
# checkpointed step to a node.
_CHANNEL_TO_NODE = {
    "summary": "doc_summarizer",
    "risk_flags": "risk_flagger",
    "ic_memo_draft": "ic_memo_drafter",
    "pricing_note": "pricing_advisor",
}


def list_activity(limit: int = 50) -> list[dict[str, Any]]:
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(
            """
            select thread_id,
                   checkpoint_id,
                   checkpoint->'updated_channels' as updated_channels,
                   checkpoint->>'ts' as ts,
                   checkpoint->'channel_values' as channel_values,
                   metadata
            from checkpoints
            order by checkpoint_id desc
            limit %s
            """,
            (limit * 10,),  # each run writes ~9 checkpoint rows; only some map to a node
        )
        rows = cur.fetchall()

    events: list[dict[str, Any]] = []
    for row in rows:
        updated = row["updated_channels"] or []
        # A single checkpoint can carry writes from more than one node — the
        # fan-out step (ic_memo_drafter + pricing_advisor run in parallel,
        # agents/graph.py's Send()) writes both `ic_memo_draft` and
        # `pricing_note` into the same checkpoint, so this must emit one
        # event per matched node, not just the first channel found.
        nodes = dict.fromkeys(_CHANNEL_TO_NODE[ch] for ch in updated if ch in _CHANNEL_TO_NODE)
        if not nodes:
            continue

        channel_values = row["channel_values"] or {}
        deal_id, _, document_id = row["thread_id"].partition(":")

        for node in nodes:
            status = "failed" if node == "pricing_advisor" and channel_values.get("pricing_error") else "success"
            events.append(
                {
                    "thread_id": row["thread_id"],
                    "deal_id": deal_id,
                    "document_id": document_id or None,
                    "node": node,
                    "status": status,
                    "ts": row["ts"],
                    "step": (row["metadata"] or {}).get("step"),
                }
            )

    events.sort(key=lambda e: e["ts"], reverse=True)
    return events[:limit]
