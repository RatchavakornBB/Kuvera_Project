"""Fetches a document's real bytes from Supabase Storage for a node to pass
to Claude as a native content block (system-architecture.md Section 5.4) —
no separate text-extraction step, Claude reads the PDF directly."""

from agents.db import get_client

BUCKET = "deal-documents"

_MEDIA_TYPES = {
    "pdf": "application/pdf",
}


def fetch_document(document_id: str) -> tuple[bytes, str, str]:
    """Returns (file_bytes, filename, media_type)."""
    client = get_client()
    row = client.table("documents").select("name, storage_path").eq("id", document_id).execute().data
    if not row:
        raise ValueError(f"No document with id {document_id}")
    name, storage_path = row[0]["name"], row[0]["storage_path"]
    if not storage_path:
        raise ValueError(f"Document {document_id} has no storage_path (upload incomplete)")

    content = client.storage.from_(BUCKET).download(storage_path)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    media_type = _MEDIA_TYPES.get(ext)
    if media_type is None:
        raise ValueError(f"Unsupported document type for direct model reading: .{ext}")
    return content, name, media_type
