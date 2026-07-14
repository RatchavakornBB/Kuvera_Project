"""/chat WebSocket — system-architecture.md Section 4.4. Request/response
over the WebSocket connection, not token streaming (D-012 — Concierge
Q&A's structured tool-use output makes true streaming meaningfully more
complex; this is timeline Section 7's own 4th cut-order item, invoked
deliberately).

deal_id is required for any answer — no deal_id means no answer, per
AGENT.md Section 11's deal_id scope invariant extended to chat.
"""

from agents.chat_memory import maybe_digest_conversation
from agents.errors import NodeFailure
from agents.nodes.orchestrator import classify_intent
from agents.nodes.stage_update import extract_stage_update
from agents.nodes.web_research import web_research
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.services import analyze as analyze_service
from app.services import chat_conversations as chat_conversations_service
from app.services import concierge as concierge_service
from app.services import deals as deals_service
from app.services import documents as documents_service

router = APIRouter(tags=["chat"])


async def _handle_message(deal_id: str | None, message: str) -> dict:
    if not deal_id:
        return {
            "role": "assistant",
            "text": "Which deal are you asking about? I can only answer questions scoped to one deal at a time.",
        }

    route = await run_in_threadpool(classify_intent, message)

    if route == "web_research":
        result = await run_in_threadpool(web_research, message)
        sources = [c["url"] for c in result["citations"] if c.get("url")]
        return {"role": "assistant", "text": result["answer"], "sources": sources}

    if route == "analyst_lead":
        doc = await run_in_threadpool(documents_service.get_latest_document, deal_id)
        if doc is None:
            return {"role": "assistant", "text": "There's no document uploaded for this deal yet to analyze."}
        result = await run_in_threadpool(analyze_service.run_analysis, deal_id, doc["id"])
        preview = result["summary"][:300].rsplit(" ", 1)[0]
        return {
            "role": "assistant",
            "text": f"Analysis complete on {doc['name']}. {preview}… (open the artifact below for the full summary, risk flags, IC memo, and pricing note)",
            "artifact": {"title": f"{doc['name']} — IC memo draft", "type": "Doc", "deal_id": deal_id},
        }

    if route == "update_stage":
        update = await run_in_threadpool(extract_stage_update, deal_id, message)
        await run_in_threadpool(deals_service.update_deal_stage, deal_id, update["stage"])
        return {"role": "assistant", "text": update["confirmation"]}

    result = await run_in_threadpool(concierge_service.ask_about_deal, deal_id, message)
    return {"role": "assistant", "text": result["answer"], "sources": result.get("sources", [])}


@router.websocket("/chat")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            deal_id = data.get("deal_id")
            conversation_id = data.get("conversation_id")

            # Real episodic memory: every conversation is persisted, not just
            # held in client-side React state. Auto-create one on first
            # message if the frontend didn't already have one open (a new
            # deal-scoped chat "tab").
            if deal_id:
                if not conversation_id:
                    convo = await run_in_threadpool(chat_conversations_service.create_conversation, deal_id)
                    conversation_id = convo["id"]
                await run_in_threadpool(
                    chat_conversations_service.save_message, conversation_id, "user", message
                )

            try:
                response = await _handle_message(deal_id, message)
            except NodeFailure as e:
                response = {"role": "assistant", "text": f"Something went wrong: {e.reason} ({e.raw_error})"}

            if deal_id:
                response["conversation_id"] = conversation_id
                await run_in_threadpool(
                    chat_conversations_service.save_message,
                    conversation_id,
                    "assistant",
                    response["text"],
                    response.get("sources"),
                    response.get("artifact"),
                )

            await websocket.send_json(response)

            if deal_id:
                # Best-effort, fires only every DIGEST_TRIGGER_MESSAGE_COUNT
                # genuinely new messages — runs after the reply is already
                # sent so it never adds latency to the user-visible answer.
                await run_in_threadpool(maybe_digest_conversation, conversation_id)
    except WebSocketDisconnect:
        pass
