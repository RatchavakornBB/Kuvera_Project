"""'Ask about this deal' — ux-ui-spec.md Section 3.2 persistent side panel.
Deal-scoped Q&A, synchronous REST for now; the /chat WebSocket (phase3-004)
routes here internally for deal-scoped questions rather than duplicating
this logic."""

from agents.errors import NodeFailure
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import concierge as concierge_service
from app.services import deals as deals_service

router = APIRouter(prefix="/deals", tags=["concierge"])


class AskRequest(BaseModel):
    question: str


@router.post("/{deal_id}/ask")
def ask_about_deal(deal_id: str, body: AskRequest):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    try:
        return concierge_service.ask_about_deal(deal_id=deal_id, question=body.question)
    except NodeFailure as e:
        raise HTTPException(status_code=500, detail=e.to_dict()) from e
