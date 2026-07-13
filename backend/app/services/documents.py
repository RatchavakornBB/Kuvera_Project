"""The one write path for the documents resource. Every upload creates a
Storage object AND a Document row together — never one without the other
(AGENT.md Section 11 invariant). If the DB insert fails after the storage
upload succeeds, the storage object is removed rather than left orphaned.
"""

import uuid
from typing import Any

from app.db import get_client

BUCKET = "deal-documents"


def upload_document(deal_id: str, filename: str, content: bytes, content_type: str) -> dict[str, Any]:
    client = get_client()
    storage_path = f"{deal_id}/{uuid.uuid4()}-{filename}"

    client.storage.from_(BUCKET).upload(
        storage_path, content, {"content-type": content_type}
    )

    try:
        res = (
            client.table("documents")
            .insert(
                {
                    "deal_id": deal_id,
                    "name": filename,
                    "type": _infer_type(filename),
                    "storage_path": storage_path,
                    "status": "received",
                }
            )
            .execute()
        )
    except Exception:
        client.storage.from_(BUCKET).remove([storage_path])
        raise

    return res.data[0]


def list_documents(
    deal_id: str | None = None,
    doc_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    client = get_client()
    query = client.table("documents").select("*, deal:deals(id, name)")
    if deal_id:
        query = query.eq("deal_id", deal_id)
    if doc_type:
        query = query.eq("type", doc_type)
    if status:
        query = query.eq("status", status)
    docs = query.order("uploaded_at", desc=True).execute().data

    if q:
        # Filtered in Python (not a `.or_()` ilike filter) so an arbitrary user
        # search string never has to be interpolated into a PostgREST filter
        # expression — small dataset at this scale, correctness over a query-
        # level filter here.
        needle = q.lower()
        docs = [d for d in docs if needle in (d["name"] or "").lower() or needle in (d.get("summary") or "").lower()]

    return docs


def get_document(document_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = client.table("documents").select("*").eq("id", document_id).execute()
    return res.data[0] if res.data else None


def get_latest_document(deal_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = (
        client.table("documents")
        .select("*")
        .eq("deal_id", deal_id)
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _infer_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "pdf": "PDF",
        "xlsx": "Financial",
        "xls": "Financial",
        "doc": "Document",
        "docx": "Document",
        "png": "Image",
        "jpg": "Image",
        "jpeg": "Image",
        "mp3": "Audio",
        "mp4": "Video",
    }.get(ext, "Document")
