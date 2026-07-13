from fastapi import APIRouter, HTTPException, UploadFile

from app.services import deals as deals_service
from app.services import documents as documents_service

router = APIRouter(prefix="/deals", tags=["documents"])
library_router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{deal_id}/documents")
async def upload_document(deal_id: str, file: UploadFile):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    content = await file.read()
    return documents_service.upload_document(
        deal_id=deal_id,
        filename=file.filename or "upload",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )


@library_router.get("")
def list_documents(deal_id: str | None = None, type: str | None = None, status: str | None = None, q: str | None = None):
    return documents_service.list_documents(deal_id=deal_id, doc_type=type, status=status, q=q)
