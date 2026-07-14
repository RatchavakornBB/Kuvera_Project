from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import chat_conversations as chat_conversations_service
from app.services import deals as deals_service

router = APIRouter(prefix="/deals", tags=["chat-conversations"])
library_router = APIRouter(prefix="/conversations", tags=["chat-conversations"])


class ConversationCreate(BaseModel):
    title: str | None = None


@router.get("/{deal_id}/conversations")
def list_conversations(deal_id: str):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return chat_conversations_service.list_conversations(deal_id)


@router.post("/{deal_id}/conversations")
def create_conversation(deal_id: str, body: ConversationCreate):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return chat_conversations_service.create_conversation(deal_id, title=body.title)


@library_router.get("/{conversation_id}/messages")
def get_messages(conversation_id: str):
    if chat_conversations_service.get_conversation(conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return chat_conversations_service.get_messages(conversation_id)


@library_router.post("/backfill-embeddings")
def backfill_embeddings():
    return {"embedded_count": chat_conversations_service.backfill_missing_message_embeddings()}
