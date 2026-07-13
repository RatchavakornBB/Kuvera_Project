from typing import Any

from agents.contradictions import list_contradictions, resolve_contradiction


def list_for_deal(deal_id: str) -> list[dict[str, Any]]:
    return list_contradictions(deal_id)


def resolve(contradiction_id: str, resolution: str, note: str) -> dict[str, Any]:
    return resolve_contradiction(contradiction_id, resolution, note)
