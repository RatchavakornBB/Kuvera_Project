"""The one write path for the documents resource. Every upload creates a
Storage object AND a Document row together — never one without the other
(AGENT.md Section 11 invariant). If the DB insert fails after the storage
upload succeeds, the storage object is removed rather than left orphaned.
"""

import re
import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row

from agents.config import settings
from agents.embeddings import embed_text, embed_texts
from agents.web_source import fetch_url_as_text

from app.db import get_client

BUCKET = "deal-documents"

# Every read path uses this explicit list rather than "*" — documents.embedding
# is a 1024-float vector and has no business appearing in an API response.
DOCUMENT_COLUMNS = (
    "id, deal_id, name, type, storage_path, status, summary, key_date, clauses, source_url, "
    "uploaded_at, created_at"
)


def _embed_document_text(text: str) -> list[float] | None:
    """Best-effort — an embeddings-provider failure (rate limit, network) must
    never break an upload or a summary write, so this swallows its own
    errors and returns None. A document with no embedding simply won't
    surface in semantic search until it's re-embedded (see
    backfill_missing_embeddings)."""
    if not text.strip():
        return None
    try:
        return embed_text(text, input_type="document")
    except Exception:
        return None


def upload_document(
    deal_id: str, filename: str, content: bytes, content_type: str, source_url: str | None = None
) -> dict[str, Any]:
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
                    "type": "Link" if source_url else _infer_type(filename),
                    "storage_path": storage_path,
                    "status": "received",
                    "source_url": source_url,
                    "embedding": _embed_document_text(filename),
                }
            )
            .execute()
        )
    except Exception:
        client.storage.from_(BUCKET).remove([storage_path])
        raise

    doc = res.data[0]
    doc.pop("embedding", None)
    return doc


def create_document_from_url(deal_id: str, url: str) -> dict[str, Any]:
    """NotebookLM-style "add a link" source — fetches the real page content
    server-side (agents/web_source.py, includes SSRF protection) and stores
    it through the exact same real write path as a file upload, just with
    source_url set for provenance. The extracted text is stored as a real
    .txt document, which agents/documents.py::build_content_block() already
    knows how to feed to Claude — link sources are just as analyzable as an
    uploaded file, not a lesser citation-only stub.

    Also runs a real doc_summarizer call immediately (just that one node,
    not the full Analyst Lead pipeline — risk-flagging/IC-memo/pricing
    don't make sense for a general reference URL) so the source is
    genuinely readable by Concierge Q&A right away, matching NotebookLM's
    real behavior. agents/deal_context.py::build_deal_context() only ever
    surfaces a document's `summary` field to Concierge, never raw bytes —
    without this, a freshly-added link would sit invisible to Concierge
    until someone separately ran Analyze on it. Best-effort: a
    summarization failure here does not fail the whole add-link action,
    since the document itself was already created successfully — it just
    leaves `summary` null, same as any document nobody has analyzed yet."""
    title, text = fetch_url_as_text(url)
    safe_title = re.sub(r"[^\w\s.-]", "", title).strip()[:80] or "web-source"
    filename = f"{safe_title}.txt"
    doc = upload_document(deal_id, filename, text.encode("utf-8"), "text/plain", source_url=url)

    try:
        from agents.nodes.doc_summarizer import doc_summarizer

        result = doc_summarizer({"document_id": doc["id"]})
        update_document_summary(doc["id"], {"summary": result["summary"]})
        doc["summary"] = result["summary"]
    except Exception:
        pass

    return doc


def update_document_summary(document_id: str, fields: dict[str, Any]) -> None:
    """Called after doc_summarizer/contract_summarizer write a real summary —
    re-embeds on the stronger name+summary text so semantic search reflects
    actual document content, not just the filename from upload time."""
    client = get_client()
    doc = get_document(document_id)
    name = fields.get("name") or (doc["name"] if doc else "")
    summary = fields.get("summary") or ""
    fields = {**fields, "embedding": _embed_document_text(f"{name}\n{summary}")}
    client.table("documents").update(fields).eq("id", document_id).execute()


def backfill_missing_embeddings() -> int:
    """One-time/on-demand catch-up for documents that predate this migration
    or whose embed call failed at write time (e.g. a real Voyage rate limit).
    Not wired to a schedule — this is a maintenance action, not a recurring
    job. Batches every text into ONE Voyage call (embed_texts), not one call
    per doc — a free-tier Voyage key's low requests-per-minute limit makes
    the per-record version hit a real 429, the exact failure mode this was
    written to avoid (see agents/embeddings.py's own docstring, and the same
    lesson learned the hard way during phase5-009's knowledge_base
    promotion)."""
    client = get_client()
    docs = client.table("documents").select("id, name, summary").is_("embedding", "null").execute().data
    if not docs:
        return 0
    texts = [f"{doc['name']}\n{doc.get('summary') or ''}" for doc in docs]
    try:
        embeddings = embed_texts(texts, input_type="document")
    except Exception:
        return 0
    count = 0
    for doc, embedding in zip(docs, embeddings):
        client.table("documents").update({"embedding": embedding}).eq("id", doc["id"]).execute()
        count += 1
    return count


def list_documents(
    deal_id: str | None = None,
    doc_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    if q:
        return _search_documents(q, deal_id=deal_id, doc_type=doc_type, status=status)

    client = get_client()
    query = client.table("documents").select(f"{DOCUMENT_COLUMNS}, deal:deals(id, name)")
    if deal_id:
        query = query.eq("deal_id", deal_id)
    if doc_type:
        query = query.eq("type", doc_type)
    if status:
        query = query.eq("status", status)
    return query.order("uploaded_at", desc=True).execute().data


def _search_documents(
    q: str, deal_id: str | None, doc_type: str | None, status: str | None, limit: int = 30
) -> list[dict[str, Any]]:
    """Real pgvector cosine search (reuses the Voyage AI infra from
    agents/embeddings.py — same model, same pipeline the Knowledge Agent
    uses, not a second one). Direct psycopg connection, matching
    agents/knowledge.py::search_knowledge's pattern, since PostgREST has no
    vector-distance operator support. Rows with no embedding yet (a real
    Voyage failure at write time, or a doc that predates this migration —
    see backfill_missing_embeddings) are excluded rather than silently
    ranked last with a meaningless distance."""
    query_embedding = embed_text(q, input_type="query")
    embedding_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"

    conditions = ["embedding is not null"]
    params: list[Any] = []
    if deal_id:
        conditions.append("deal_id = %s")
        params.append(deal_id)
    if doc_type:
        conditions.append("type = %s")
        params.append(doc_type)
    if status:
        conditions.append("status = %s")
        params.append(status)
    where_clause = " and ".join(conditions)

    select_cols = ", ".join(f"d.{col.strip()}" for col in DOCUMENT_COLUMNS.split(","))
    sql = f"""
        select {select_cols}, deals.id as deal_pk_id, deals.name as deal_name
        from public.documents d
        join public.deals deals on deals.id = d.deal_id
        where {where_clause}
        order by d.embedding <=> %s::vector
        limit %s
    """
    params = [*params, embedding_literal, limit]

    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    for row in rows:
        deal_id_val = row.pop("deal_pk_id")
        deal_name_val = row.pop("deal_name")
        row["deal"] = {"id": str(deal_id_val), "name": deal_name_val}
    return rows


def get_document(document_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = client.table("documents").select(DOCUMENT_COLUMNS).eq("id", document_id).execute()
    return res.data[0] if res.data else None


def download_document(document_id: str) -> tuple[bytes, str] | None:
    """Backend-mediated download — the Storage bucket is private on purpose
    (no direct public URLs, per the bucket migration's own note), so every
    download goes through here rather than a client-side signed URL."""
    doc = get_document(document_id)
    if doc is None or not doc.get("storage_path"):
        return None
    client = get_client()
    content = client.storage.from_(BUCKET).download(doc["storage_path"])
    return content, doc["name"]


def get_latest_document(deal_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = (
        client.table("documents")
        .select(DOCUMENT_COLUMNS)
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
