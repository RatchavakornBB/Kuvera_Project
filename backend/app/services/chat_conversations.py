"""Real persistent episodic chat memory — every conversation turn is stored
(chat_conversations + chat_messages) and embedded immediately (Voyage AI,
same pipeline as documents/knowledge_base), so a deal's chat history
survives a page refresh, supports multiple concurrent conversation
"tabs" per deal, and is real-time searchable via RAG (search_chat_history
in agents/knowledge.py) rather than living only in ephemeral React state.
"""

from datetime import datetime, timezone
from typing import Any

from agents.embeddings import embed_text, embed_texts

from app.db import get_client

DEFAULT_TITLE = "New conversation"


def _embed_message(text: str) -> list[float] | None:
    """Best-effort — an embeddings-provider failure must never break sending
    a chat message, matching the existing pattern in
    backend/app/services/documents.py."""
    if not text.strip():
        return None
    try:
        return embed_text(text, input_type="document")
    except Exception:
        return None


def create_conversation(deal_id: str, title: str | None = None) -> dict[str, Any]:
    client = get_client()
    res = (
        client.table("chat_conversations")
        .insert({"deal_id": deal_id, "title": title or DEFAULT_TITLE})
        .execute()
    )
    return res.data[0]


def list_conversations(deal_id: str) -> list[dict[str, Any]]:
    client = get_client()
    return (
        client.table("chat_conversations")
        .select("id, deal_id, title, digested_message_count, created_at, last_message_at")
        .eq("deal_id", deal_id)
        .order("last_message_at", desc=True)
        .execute()
        .data
    )


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    client = get_client()
    res = (
        client.table("chat_conversations")
        .select("id, deal_id, title, digested_message_count, created_at, last_message_at")
        .eq("id", conversation_id)
        .execute()
    )
    return res.data[0] if res.data else None


def get_messages(conversation_id: str) -> list[dict[str, Any]]:
    client = get_client()
    return (
        client.table("chat_messages")
        .select("id, conversation_id, role, text, sources, artifact, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
        .data
    )


def save_message(
    conversation_id: str,
    role: str,
    text: str,
    sources: list[str] | None = None,
    artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    client = get_client()
    res = (
        client.table("chat_messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "role": role,
                "text": text,
                "sources": sources,
                "artifact": artifact,
                "embedding": _embed_message(text),
            }
        )
        .execute()
    )
    client.table("chat_conversations").update(
        {"last_message_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", conversation_id).execute()

    # First real user message becomes the conversation's title if it still
    # has the generic default — the same "auto-title from first message"
    # pattern most chat UIs use, so tabs are identifiable at a glance
    # instead of a wall of "New conversation" labels.
    if role == "user":
        convo = get_conversation(conversation_id)
        if convo and convo["title"] == DEFAULT_TITLE:
            new_title = text.strip()[:60]
            client.table("chat_conversations").update({"title": new_title}).eq(
                "id", conversation_id
            ).execute()

    message = res.data[0]
    message.pop("embedding", None)
    return message


def backfill_missing_message_embeddings() -> int:
    """One-time/on-demand catch-up for chat messages whose real-time embed
    call failed (e.g. a real Voyage rate limit — a genuine risk here since,
    unlike documents.py's batch backfill, chat messages arrive one at a
    time in real conversation and can't be pre-batched). Batches every
    text into ONE Voyage call, the same fix already applied to
    documents.py's version of this exact problem — confirmed live during
    this feature's own testing: a rapid 5-question test conversation (10
    messages) hit Voyage's rate limit on 8 of them."""
    client = get_client()
    msgs = client.table("chat_messages").select("id, text").is_("embedding", "null").execute().data
    if not msgs:
        return 0
    texts = [m["text"] for m in msgs]
    try:
        embeddings = embed_texts(texts, input_type="document")
    except Exception:
        return 0
    count = 0
    for msg, embedding in zip(msgs, embeddings):
        client.table("chat_messages").update({"embedding": embedding}).eq("id", msg["id"]).execute()
        count += 1
    return count
