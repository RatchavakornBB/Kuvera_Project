from typing import Any

from agents.drafting_lead import draft_and_store_ic_deck, draft_and_store_ic_memo, draft_cover_email, draft_notebooklm_summary


def draft_memo(deal_id: str) -> dict[str, Any]:
    return draft_and_store_ic_memo(deal_id)


def draft_deck(deal_id: str) -> dict[str, Any]:
    return draft_and_store_ic_deck(deal_id)


def draft_email(deal_id: str) -> dict[str, Any]:
    return {"email": draft_cover_email(deal_id)}


def draft_summary(deal_id: str) -> dict[str, Any]:
    return {"summary": draft_notebooklm_summary(deal_id)}
