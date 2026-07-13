from agents.errors import NodeFailure
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import analyze as analyze_service
from app.services import deals as deals_service
from app.services import documents as documents_service

router = APIRouter(prefix="/deals", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    document_id: str


@router.get("/{deal_id}/analysis")
def get_latest_analysis(deal_id: str):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return analyze_service.get_latest_analysis(deal_id)


@router.post("/{deal_id}/analyze")
def analyze_deal(deal_id: str, body: AnalyzeRequest):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    # AGENT.md Section 11: never blend data across deals. document_id arrives
    # in the request body, independent of the deal_id path param — without
    # this check, a caller could point one deal's analyze call at another
    # deal's document, and the result would be saved under the wrong deal_id.
    document = documents_service.get_document(body.document_id)
    if document is None or document["deal_id"] != deal_id:
        raise HTTPException(status_code=404, detail="Document not found for this deal")

    try:
        return analyze_service.run_analysis(deal_id=deal_id, document_id=body.document_id)
    except NodeFailure as e:
        # AGENT.md Section 10: tell the user explicitly which node, which
        # attempt, and the actual error — never a generic 500 with no detail.
        raise HTTPException(status_code=500, detail=e.to_dict()) from e
