import mimetypes
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from agents.web_source import UnsafeUrlError

from app.services import deals as deals_service
from app.services import documents as documents_service

router = APIRouter(prefix="/deals", tags=["documents"])
library_router = APIRouter(prefix="/documents", tags=["documents"])


class AddLinkSource(BaseModel):
    url: str


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


@router.post("/{deal_id}/documents/from-url")
def add_link_source(deal_id: str, body: AddLinkSource):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    try:
        return documents_service.create_document_from_url(deal_id, body.url)
    except UnsafeUrlError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Could not fetch that URL: {e}") from e


@library_router.get("")
def list_documents(deal_id: str | None = None, type: str | None = None, status: str | None = None, q: str | None = None):
    return documents_service.list_documents(deal_id=deal_id, doc_type=type, status=status, q=q)


@library_router.post("/backfill-embeddings")
def backfill_embeddings():
    return {"embedded_count": documents_service.backfill_missing_embeddings()}


@library_router.get("/{document_id}/download")
def download_document(document_id: str):
    result = documents_service.download_document(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found or has no stored file")
    content, filename = result
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    # Content-Disposition's plain filename= param is Latin-1 only (HTTP header
    # values are) — a Thai/Unicode filename (e.g. from a fetched page's <title>)
    # raises a real UnicodeEncodeError there, not a fabricated edge case. The
    # RFC 6266 fix: an ASCII-safe fallback plus a UTF-8 percent-encoded
    # filename* that real browsers prefer and display correctly.
    ascii_fallback = filename.encode("ascii", "replace").decode("ascii")
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename)}"
        },
    )
