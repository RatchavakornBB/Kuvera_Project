"""The one write path for the documents resource. Every upload creates a
Storage object AND a Document row together — never one without the other
(AGENT.md Section 11 invariant). If the DB insert fails after the storage
upload succeeds, the storage object is removed rather than left orphaned.
"""

import re
import threading
import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row

from agents.config import settings
from agents.embeddings import embed_text, embed_texts
from agents.web_source import fetch_url_content

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


def _storage_safe_filename(filename: str) -> str:
    """Supabase Storage rejects non-ASCII object keys (a real 400 InvalidKey
    from the storage API, not an SSRF/permissions issue) — filenames derived
    from a page <title> (create_document_from_url) or a chat question
    (create_document_from_research) can be Thai/any-Unicode text, so the
    storage key needs its own ASCII-safe slug. The human-readable `name`
    column stores the original filename unchanged; only the storage key is
    transliterated here."""
    base, dot, ext = filename.rpartition(".")
    base = base if dot else filename
    ext = f".{ext}" if dot else ""
    safe_base = re.sub(r"\s+", " ", base.encode("ascii", "ignore").decode("ascii")).strip(" -_")
    return f"{safe_base or 'file'}{ext}"


def upload_document(
    deal_id: str, filename: str, content: bytes, content_type: str, source_url: str | None = None
) -> dict[str, Any]:
    client = get_client()
    storage_path = f"{deal_id}/{uuid.uuid4()}-{_storage_safe_filename(filename)}"

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
    """NotebookLM-style "add a link" source — fetches the real content
    server-side (agents/web_source.py, includes SSRF protection) and stores
    it through the exact same real write path as a file upload, just with
    source_url set for provenance.

    Two real shapes, per agents/web_source.py::fetch_url_content:
    - A webpage: extracted readable text, stored as a real .txt document.
    - A URL pointing directly at a PDF/.docx/image: the real file bytes,
      stored exactly like an uploaded file — a link to a PDF is just as
      analyzable as an uploaded PDF, not downgraded to a citation stub
      because it arrived via URL instead of a file picker.

    Either way, agents/documents.py::build_content_block() already knows
    how to feed the result to Claude, so the same doc_summarizer call
    below works unmodified regardless of which branch produced the
    document.

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
    result = fetch_url_content(url)
    if result["kind"] == "text":
        safe_title = re.sub(r"[^\w\s.-]", "", result["title"]).strip()[:80] or "web-source"
        filename = f"{safe_title}.txt"
        doc = upload_document(deal_id, filename, result["text"].encode("utf-8"), "text/plain", source_url=url)
    else:
        doc = upload_document(deal_id, result["filename"], result["content"], result["content_type"], source_url=url)

    try:
        from agents.nodes.doc_summarizer import doc_summarizer

        summary_result = doc_summarizer({"document_id": doc["id"]})
        update_document_summary(doc["id"], {"summary": summary_result["summary"]})
        doc["summary"] = summary_result["summary"]
    except Exception:
        pass

    return doc


def _refresh_document_from_url(doc_id: str, storage_path: str, url: str) -> None:
    """Re-fetches url and overwrites the existing document's stored bytes
    and summary in place — storage3's update() is a PUT that overwrites,
    unlike upload()'s POST which fails if the key already exists. For a
    source whose content changes over time (a live stock-price page, a
    developing news story), this keeps the saved citation's own content
    current instead of calcifying at whatever it was on first fetch, while
    web_research's web_search/web_fetch calls that produced the chat answer
    were already fresh regardless — this only refreshes the stored copy."""
    result = fetch_url_content(url)
    if result["kind"] == "text":
        content, content_type = result["text"].encode("utf-8"), "text/plain"
    else:
        content, content_type = result["content"], result["content_type"]

    client = get_client()
    client.storage.from_(BUCKET).update(storage_path, content, {"content-type": content_type})

    from agents.nodes.doc_summarizer import doc_summarizer

    summary_result = doc_summarizer({"document_id": doc_id})
    update_document_summary(doc_id, {"summary": summary_result["summary"]})


def _save_new_citation_links(deal_id: str, urls: list[str]) -> None:
    """Fetches each cited URL as its own real Link document (same path as a
    manual "Add link"), so a chat research answer leaves behind the actual
    underlying sources — independently downloadable/re-analyzable — not
    just a list of URLs sitting inside one synthesized note.

    Matched against source_urls already saved for this deal: a URL cited
    again gets its existing document's content refreshed in place
    (_refresh_document_from_url) rather than skipped or duplicated, since
    the same popular article gets re-cited across multiple research
    questions and its content may have changed since it was first saved.

    Best-effort per URL: one citation failing to fetch/refresh (paywall,
    bot-block like investing.com's 403, a since-dead link) must not fail
    the research note itself, which is already the primary, reliable
    artifact."""
    if not urls:
        return
    client = get_client()
    existing = (
        client.table("documents")
        .select("id, source_url, storage_path")
        .eq("deal_id", deal_id)
        .not_.is_("source_url", "null")
        .execute()
        .data
    )
    existing_by_url = {row["source_url"]: row for row in existing}
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        try:
            if url in existing_by_url:
                row = existing_by_url[url]
                _refresh_document_from_url(row["id"], row["storage_path"], url)
            else:
                create_document_from_url(deal_id, url)
        except Exception:
            pass


def create_document_from_research(
    deal_id: str, question: str, answer: str, citations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Persists a chat web_research answer as a real, RAG-searchable
    Document — previously this was pure chat-transcript ephemera (see
    agents/nodes/web_research.py's own docstring: it returns {answer,
    citations} and writes nothing itself). Reuses the same upload_document
    write path as every other document type and embeds on name+summary
    like update_document_summary does for everything else, so a research
    answer surfaces in Documents search and Concierge Q&A's deal_context
    exactly like an uploaded file or an added link — not a second-class
    citation-only stub. Also saves each individual citation as its own Link
    document via _save_new_citation_links, so the sources aren't just a URL
    list inside this note — fired on a background thread (not awaited) since
    it can fetch+summarize several citation URLs one at a time, and this
    function is called synchronously from the chat websocket handler while
    the user is waiting on the answer that already arrived; the citation
    links appearing a few seconds later beats making the whole chat turn
    stall on them (real observed symptom: a from-chat question hung the
    websocket for the entire fetch+summarize loop before this fix)."""
    safe_title = re.sub(r"[^\w\s.-]", "", question).strip()[:80] or "web-research"
    filename = f"{safe_title}.txt"

    lines = [f"QUESTION: {question}", "", "ANSWER:", answer]
    urls = [c["url"] for c in citations if c.get("url")]
    if urls:
        lines += ["", "SOURCES:"] + [f"- {u}" for u in urls]
    content = "\n".join(lines)

    # Only set source_url (a single-URL provenance field) when there's
    # exactly one citation — multiple sources are listed in the body
    # instead of picking one arbitrarily to elevate.
    source_url = urls[0] if len(urls) == 1 else None
    doc = upload_document(deal_id, filename, content.encode("utf-8"), "text/plain", source_url=source_url)
    update_document_summary(doc["id"], {"summary": answer[:2000], "type": "Research"})
    threading.Thread(target=_save_new_citation_links, args=(deal_id, urls), daemon=True).start()
    doc["summary"] = answer[:2000]
    doc["type"] = "Research"
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


def get_latest_document(deal_id: str, doc_type: str | None = None) -> dict[str, Any] | None:
    client = get_client()
    query = client.table("documents").select(DOCUMENT_COLUMNS).eq("deal_id", deal_id)
    if doc_type:
        query = query.eq("type", doc_type)
    res = query.order("uploaded_at", desc=True).limit(1).execute()
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
