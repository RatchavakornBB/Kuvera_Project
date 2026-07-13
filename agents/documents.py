"""Fetches a document's real bytes from Supabase Storage for a node to pass
to Claude as a native content block (system-architecture.md Section 5.4) —
no separate text-extraction step, Claude reads the file directly.

PDF and images are both real, native Claude Messages API input types (a
`document` block and an `image` block respectively) — genuinely supported,
not stubs. Audio and video are NOT extended here: Claude's Messages API has
no native audio/video content block, so "supporting" them would mean either
silently failing later or fabricating a transcription/frame-extraction
pipeline that doesn't exist. They still raise a clear error at fetch time."""

from typing import Any

from agents.db import get_client

BUCKET = "deal-documents"

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}

# Claude's Messages API content block "type" differs by media_type — a PDF is
# a `document` block, an image is an `image` block. Everything else in
# _MEDIA_TYPES that isn't application/pdf is an image, by construction.


def build_content_block(content: bytes, media_type: str) -> dict[str, Any]:
    """The one place a document's bytes become a Claude content block —
    every document-reading node uses this instead of hardcoding the block
    shape, so adding a new supported media_type never requires a node edit."""
    import base64

    block_type = "document" if media_type == "application/pdf" else "image"
    return {
        "type": block_type,
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(content).decode(),
        },
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
        raise ValueError(
            f"Unsupported document type for direct model reading: .{ext} "
            "(PDF and images are supported; audio/video have no native Claude "
            "Messages API content type, not just missing glue code here)"
        )
    return content, name, media_type
