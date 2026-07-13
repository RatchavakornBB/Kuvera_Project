from agents.errors import NodeFailure
from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.services import contracts as contracts_service
from app.services import deals as deals_service

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("")
async def upload_contract(file: UploadFile, deal_id: str = Form(...)):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    content = await file.read()
    try:
        return contracts_service.process_contract(
            deal_id=deal_id,
            filename=file.filename or "contract",
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
    except NodeFailure as e:
        raise HTTPException(status_code=500, detail=e.to_dict()) from e
