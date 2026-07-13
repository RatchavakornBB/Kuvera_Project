from agents.errors import NodeFailure
from fastapi import APIRouter, HTTPException

from app.services import deals as deals_service
from app.services import drafting as drafting_service

router = APIRouter(prefix="/deals", tags=["drafting"])


def _require_deal(deal_id: str) -> None:
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")


@router.post("/{deal_id}/draft/memo")
def draft_memo(deal_id: str):
    _require_deal(deal_id)
    try:
        return drafting_service.draft_memo(deal_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NodeFailure as e:
        raise HTTPException(status_code=500, detail=e.to_dict()) from e


@router.post("/{deal_id}/draft/deck")
def draft_deck(deal_id: str):
    _require_deal(deal_id)
    try:
        return drafting_service.draft_deck(deal_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NodeFailure as e:
        raise HTTPException(status_code=500, detail=e.to_dict()) from e


@router.post("/{deal_id}/draft/email")
def draft_email(deal_id: str):
    _require_deal(deal_id)
    try:
        return drafting_service.draft_email(deal_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NodeFailure as e:
        raise HTTPException(status_code=500, detail=e.to_dict()) from e


@router.post("/{deal_id}/draft/summary")
def draft_summary(deal_id: str):
    _require_deal(deal_id)
    try:
        return drafting_service.draft_summary(deal_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NodeFailure as e:
        raise HTTPException(status_code=500, detail=e.to_dict()) from e
