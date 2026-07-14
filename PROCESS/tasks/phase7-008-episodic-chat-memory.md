Scope: supabase/migrations/<new>_create_chat_episodic_memory.sql, agents/chat_memory.py (new),
agents/nodes/concierge_qa.py, backend/app/services/chat_conversations.py (new),
backend/app/routes/chat.py, backend/app/routes/chat_conversations.py (new), backend/app/main.py,
frontend/src/lib/api.ts, frontend/src/lib/useChatSocket.ts, frontend/src/pages/ChatPage.tsx,
frontend/src/components/layout/AppShell.tsx
Depends on: agents/embeddings.py (Voyage AI, reused), agents/knowledge.py's promote_deal_to_knowledge
pattern (reused for the digest), phase7-005/006 (Sources panel this integrates into)

Scope: user asked for 4 things — (1) Chat accumulates real episodic memory from what's been asked,
(2) that memory feeds real RAG, (3) Knowledge gets a route that collects and summarizes it
further, (4) multiple conversation "tabs" per deal. Clarified two architecture decisions before
building (embedding granularity, digest trigger mechanism — both affect real ongoing API cost)
and got explicit answers: embed every message immediately, auto-digest triggered by real activity
(every N messages) rather than a blind timer.

DoD:
  - [x] `chat_conversations` + `chat_messages` tables (real persistence — chat state was
        previously pure in-memory React state, confirmed via a dedicated research pass before
        this task that it had zero DB backing at all)
  - [x] Every message embedded immediately on save (Voyage AI, same pipeline as
        documents/knowledge_base) — per the user's explicit choice
  - [x] `agents/chat_memory.py::search_chat_history()` — real pgvector cosine search over a deal's
        chat_messages, scoped by deal_id (the same invariant every other retrieval path enforces)
  - [x] `chat_history_context()` wired into `agents/nodes/concierge_qa.py::_run_once()` — Concierge
        now genuinely recalls relevant past exchanges, not just structured deal data, verified by
        a real answer that referenced actual prior conversation content
  - [x] `agents/chat_memory.py::maybe_digest_conversation()` — real Claude synthesis call
        (mirrors `promote_deal_to_knowledge`'s pattern) that distills a stretch of conversation into
        a structured `knowledge_base` record under a new `chat_insights` category, fires
        automatically once `DIGEST_TRIGGER_MESSAGE_COUNT` (10) genuinely new messages have
        accumulated since the last digest — tied to real activity, not a blind schedule
  - [x] `/chat` WebSocket now persists both the user message and assistant response every turn,
        auto-creates a conversation on first message if none was supplied, returns
        `conversation_id` to the frontend, and triggers the digest check after replying (so digest
        latency never delays the user-visible answer)
  - [x] `GET/POST /deals/{deal_id}/conversations`, `GET /conversations/{id}/messages` — real REST
        surface for listing/creating conversations and loading a conversation's persisted history
  - [x] Frontend: `useChatSocket` gained `conversationId`/`switchConversation`/
        `startNewConversation`; `ChatPage.tsx` renders a real tab strip per selected deal
        (auto-selects the most recent conversation on deal switch, or starts fresh if none exist),
        each tab auto-titled from its first real user message, "+" starts a genuinely new thread
  - [x] Verified past "no error thrown" with two real bugs found and fixed along the way, not just
        a clean run assumed to be correct:
        1. Real 5-turn WebSocket test (bypassing the UI, driving the actual `/chat` protocol
           directly) proved conversation continuity (same `conversation_id` across all 5 turns)
           and, critically, that RAG recall genuinely works: asking "Summarize what we've discussed
           so far" produced a real answer that referenced actual prior exchange content pulled from
           `chat_history_context()`, not a fabricated summary.
        2. Direct DB inspection after that test found only 2 of 10 messages had a real embedding —
           traced to Voyage's rate limit under rapid-fire real-time per-message embedding (an
           inherent risk of "embed every message immediately," unlike documents.py's batchable
           backfill case). Fixed by adding `backfill_missing_message_embeddings()` (batches every
           null-embedding message into ONE Voyage call, same fix pattern already used for documents)
           + `POST /conversations/backfill-embeddings`. Verified: backfill recovered all 7 missing
           embeddings.
        3. The auto-digest silently returned `None` with zero visible error even after the rate
           limit cleared — traced by bypassing the best-effort exception swallowing directly:
           `KeyError: 'topic'`. Claude's `report_chat_digest` tool_use call omitted a real
           *required* schema field entirely — a distinct tool-use conformance failure mode from the
           earlier `clause_extractor` stringified-array quirk, but the same underlying lesson (real
           models don't always perfectly conform to a tool schema). Fixed with a fallback
           (`digest.get("topic") or convo.get("title") or "General discussion"`). Re-verified: the
           digest then succeeded, wrote a real, richly-detailed `knowledge_base` row, and correctly
           updated `digested_message_count` so the same messages are never re-digested.
        4. Real browser test: sent a message (auto-created + auto-titled tab 1), started a second
           conversation via "+" (confirmed genuinely empty, not carrying over tab 1's messages),
           sent a message in tab 2, then switched back to tab 1 and confirmed its original
           question/answer reloaded correctly from the real persisted history (a real
           `GET /conversations/{id}/messages` call, not cached client state) — zero console errors.
  - [x] All self-created test conversations, messages, and knowledge_base digest rows cleaned up
        from the database afterward.
