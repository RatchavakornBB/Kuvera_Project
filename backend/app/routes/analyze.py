from agents.errors import NodeFailure
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import analyze as analyze_service
from app.services import deals as deals_service

router = APIRouter(prefix="/deals", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    document_id: str


@router.post("/{deal_id}/analyze")
def analyze_deal(deal_id: str, body: AnalyzeRequest):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    try:
        return analyze_service.run_analysis(deal_id=deal_id, document_id=body.document_id)
    except NodeFailure as e:
        # AGENT.md Section 10: tell the user explicitly which node, which
        # attempt, and the actual error — never a generic 500 with no detail.
        raise HTTPException(status_code=500, detail=e.to_dict()) from e
