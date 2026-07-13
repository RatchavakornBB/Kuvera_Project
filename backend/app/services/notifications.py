"""4.3 Key-date notifier (system-architecture.md Section 8) — an on-demand
check, not a true scheduled background job (see PROCESS/tasks/phase4-004
for the reasoning: no task-queue infrastructure exists in this MVP, and
building one for a single feature is disproportionate to a 5-day build).
The frontend polls this on an interval instead, which is functionally
equivalent at this dataset's scale.

Only `documents.key_date` is used — `milestones.occurred_at` is retrospective
(set once a milestone happens), not a forward-looking due date, so it has
nothing to notify about."""

from datetime import date, datetime, timezone
from typing import Any

from app.db import get_client


def list_key_date_notifications(days: int = 30) -> list[dict[str, Any]]:
    client = get_client()
    docs = (
        client.table("documents")
        .select("id, deal_id, name, key_date, deal:deals(id, name)")
        .not_.is_("key_date", "null")
        .execute()
        .data
    )

    today = datetime.now(timezone.utc).date()
    notifications = []
    for doc in docs:
        key_date = date.fromisoformat(doc["key_date"])
        days_until = (key_date - today).days
        if days_until > days:
            continue
        notifications.append(
            {
                "document_id": doc["id"],
                "document_name": doc["name"],
                "deal_id": doc["deal_id"],
                "deal_name": doc["deal"]["name"] if doc["deal"] else None,
                "key_date": doc["key_date"],
                "days_until": days_until,
            }
        )

    notifications.sort(key=lambda n: n["days_until"])
    return notifications
