from typing import Any

from agents.activity_log import list_activity

from app.db import get_client


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
