from typing import Any

from agents.drafting_lead import (
    draft_and_store_cover_email,
    draft_and_store_ic_deck,
    draft_and_store_ic_memo,
    draft_and_store_nda,
    draft_and_store_notebooklm_summary,
)


def draft_memo(deal_id: str) -> dict[str, Any]:
    return draft_and_store_ic_memo(deal_id)


def draft_nda(deal_id: str) -> dict[str, Any]:
    """Manual (synchronous) re-trigger of the NDA the deal-creation flow fires
    automatically in the background — same drafter, exposed for a re-draft or
    for verifying the pipeline end to end."""
    return draft_and_store_nda(deal_id)


def draft_deck(deal_id: str) -> dict[str, Any]:
    return draft_and_store_ic_deck(deal_id)


def draft_email(deal_id: str) -> dict[str, Any]:
    return draft_and_store_cover_email(deal_id)


def draft_summary(deal_id: str) -> dict[str, Any]:
    return draft_and_store_notebooklm_summary(deal_id)
