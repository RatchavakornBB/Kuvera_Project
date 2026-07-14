"""Episodic chat memory (user-requested) — real RAG search over a deal's
persisted chat history (backend/app/services/chat_conversations.py owns
the write path; every message is embedded immediately on save), plus a
real Knowledge Agent digest that periodically synthesizes accumulated
conversation into structured knowledge_base records under the
'chat_insights' category.

Two distinct real capabilities, not one blurred together:
- search_chat_history(): direct semantic search over raw message text —
  fine-grained RAG, used to give concierge_qa recall of past exchanges.
- digest_chat_to_knowledge(): a real Claude synthesis call (same pattern
  as agents/knowledge.py::promote_deal_to_knowledge) that distills a
  stretch of conversation into one structured, higher-level knowledge_base
  entry — the KB half of the request, distinct from raw-message RAG.
"""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from agents.adapters.model_adapter import call_model
from agents.config import settings
from agents.db import get_client
from agents.embeddings import embed_text, embed_texts
from agents.retry import with_retry

DIGEST_TRIGGER_MESSAGE_COUNT = 10

DIGEST_TOOL = {
    "name": "report_chat_digest",
    "description": "Report a structured digest of the real knowledge surfaced in this conversation stretch.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "A short label for what this conversation stretch was actually about"},
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Concrete facts, decisions, or conclusions that actually came up — grounded only in the real conversation text provided, never invented",
            },
            "open_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Real questions raised in the conversation that were not resolved, if any",
            },
        },
        "required": ["topic", "key_points", "open_questions"],
    },
}

DIGEST_PROMPT = """You are the Knowledge Agent, distilling a real stretch of chat conversation
about one deal into a structured digest for firm-wide knowledge. Everything below is a real
transcript excerpt — do not invent facts not present in it. If nothing substantive came up, say so
plainly in key_points rather than padding it out. Call report_chat_digest.

CONVERSATION (deal: {deal_name}):
{transcript}
"""


def search_chat_history(deal_id: str, query_text: str, limit: int = 5) -> list[dict[str, Any]]:
    """Real pgvector cosine search over this deal's persisted chat_messages
    — scoped to deal_id, matching the deal_id invariant every other
    retrieval path in this codebase enforces (AGENT.md Section 11)."""
    if not query_text:
        return []
    query_embedding = embed_text(query_text, input_type="query")
    embedding_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = """
        select m.id, m.conversation_id, m.role, m.text, m.created_at,
               1 - (m.embedding <=> %s::vector) as similarity
        from chat_messages m
        join chat_conversations c on c.id = m.conversation_id
        where c.deal_id = %s and m.embedding is not null
        order by m.embedding <=> %s::vector
        limit %s
    """
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(sql, [embedding_literal, deal_id, embedding_literal, limit])
        return cur.fetchall()


def chat_history_context(deal_id: str, query_text: str, limit: int = 3) -> str:
    """Best-effort real retrieval for concierge_qa to inject as extra
    context — same swallow-on-failure contract as
    agents/knowledge.py::historical_precedent_context, since this is
    supplementary recall, not a required output field."""
    try:
        results = search_chat_history(deal_id, query_text, limit=limit)
    except Exception:
        return ""
    if not results:
        return ""

    lines = ["\n\nRELEVANT PAST CONVERSATION ON THIS DEAL (real, retrieved by semantic search from chat history):"]
    for r in results:
        lines.append(f"- [{r['role']}] {r['text'][:300]}")
    return "\n".join(lines)


def _load_convo_and_new_messages(conversation_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    client = get_client()
    convo = (
        client.table("chat_conversations")
        .select("id, deal_id, title, digested_message_count")
        .eq("id", conversation_id)
        .execute()
        .data
    )
    if not convo:
        return None
    convo = convo[0]

    messages = (
        client.table("chat_messages")
        .select("id, role, text, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
        .data
    )
    return convo, messages[convo["digested_message_count"]:]


def maybe_digest_conversation(conversation_id: str) -> dict[str, Any] | None:
    """Called after every saved message. Fires a real digest only once a
    conversation has accumulated DIGEST_TRIGGER_MESSAGE_COUNT genuinely new
    messages since the last digest — automatic, but tied to real activity,
    not a blind timer that fires on deals with nothing new to say.
    Best-effort: a digest failure never breaks the message-send path that
    triggered it."""
    try:
        loaded = _load_convo_and_new_messages(conversation_id)
        if loaded is None:
            return None
        convo, new_messages = loaded
        if len(new_messages) < DIGEST_TRIGGER_MESSAGE_COUNT:
            return None

        total = convo["digested_message_count"] + len(new_messages)
        return _run_digest(convo, new_messages, total_message_count=total)
    except Exception:
        return None


def force_digest_conversation(conversation_id: str) -> dict[str, Any] | None:
    """Same real synthesis as maybe_digest_conversation(), but bypasses the
    DIGEST_TRIGGER_MESSAGE_COUNT threshold — called right before a
    conversation is deleted (user-requested: nothing discussed should be
    lost just because a tab gets closed before hitting the normal
    every-10-messages cadence). Returns None if there's nothing new to
    digest (already fully digested, or genuinely empty) OR if the real
    Claude/embedding call fails — the caller decides whether a failed
    digest should still allow deletion to proceed."""
    loaded = _load_convo_and_new_messages(conversation_id)
    if loaded is None:
        return None
    convo, new_messages = loaded
    if not new_messages:
        return None

    total = convo["digested_message_count"] + len(new_messages)
    return _run_digest(convo, new_messages, total_message_count=total)


def _run_digest(convo: dict[str, Any], new_messages: list[dict[str, Any]], total_message_count: int) -> dict[str, Any]:
    client = get_client()
    deal = client.table("deals").select("id, name, industries").eq("id", convo["deal_id"]).execute().data[0]

    transcript = "\n".join(f"{m['role'].upper()}: {m['text']}" for m in new_messages)

    def _call_and_parse() -> dict[str, Any]:
        response = call_model(
            "knowledge_promoter",
            messages=[{"role": "user", "content": DIGEST_PROMPT.format(deal_name=deal["name"], transcript=transcript)}],
            tools=[DIGEST_TOOL],
            max_tokens=1536,
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "report_chat_digest":
                return block.input
        raise ValueError(f"model did not call report_chat_digest (stop_reason={response.stop_reason!r})")

    digest = with_retry("chat_digest", _call_and_parse)
    # Claude's tool_use call for this schema has been observed to omit a
    # required field entirely (not just wrong-typed, as with
    # clause_extractor's stringified-array quirk) — a real, distinct
    # tool-use conformance failure mode, defended the same way: a sane
    # fallback instead of a raw KeyError crashing an otherwise-good digest.
    topic = digest.get("topic") or convo.get("title") or "General discussion"

    summary_lines = [f"Topic: {topic}", "", "Key points:"]
    summary_lines += [f"- {p}" for p in digest.get("key_points", [])]
    if digest.get("open_questions"):
        summary_lines += ["", "Open questions:"]
        summary_lines += [f"- {q}" for q in digest["open_questions"]]
    summary = "\n".join(summary_lines)

    # Best-effort, deliberately decoupled from the real synthesis above: an
    # embeddings-provider failure here (a real Voyage 429 was hit during this
    # feature's own testing, from cumulative rapid real API usage) must not
    # discard a digest whose actual content already synthesized correctly —
    # the record is still inserted with embedding=None and stays findable by
    # every other means (source_deal_id, category), just not yet via
    # semantic search until a future backfill re-embeds it. Losing the whole
    # real synthesis over a supplementary embedding hiccup would be strictly
    # worse than a documents.py-style null-embedding row.
    try:
        embedding = embed_texts([summary], input_type="document")[0]
    except Exception:
        embedding = None

    record = (
        client.table("knowledge_base")
        .insert(
            {
                "source_deal_id": convo["deal_id"],
                "category": "chat_insights",
                "company_name": deal["name"],
                "industry": deal["industries"][0] if deal["industries"] else None,
                "content": {
                    "conversation_id": convo["id"],
                    "conversation_title": convo["title"],
                    "topic": topic,
                    "key_points": digest.get("key_points", []),
                    "open_questions": digest.get("open_questions", []),
                },
                "summary": summary,
                "embedding": embedding,
            }
        )
        .execute()
        .data[0]
    )

    client.table("chat_conversations").update({"digested_message_count": total_message_count}).eq(
        "id", convo["id"]
    ).execute()

    return record
