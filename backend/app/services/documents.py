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
