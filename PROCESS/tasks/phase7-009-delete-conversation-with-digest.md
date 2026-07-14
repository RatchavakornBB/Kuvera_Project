Scope: agents/chat_memory.py, agents/knowledge.py, backend/app/services/chat_conversations.py,
backend/app/routes/chat_conversations.py, backend/app/services/knowledge.py,
backend/app/routes/knowledge.py, frontend/src/lib/api.ts, frontend/src/pages/ChatPage.tsx
Depends on: phase7-008 (episodic chat memory — chat_conversations/chat_messages, digest mechanism)

Scope: user asked for tabs to be deletable, with the system summarizing the conversation into
memory before deletion. Reuses phase7-008's existing digest machinery (real Claude synthesis into
knowledge_base) rather than building a second summarization path, bypassing the normal
DIGEST_TRIGGER_MESSAGE_COUNT=10 threshold so a short conversation isn't lost just because it never
reached the automatic cadence.

DoD:
  - [x] `agents/chat_memory.py::force_digest_conversation()` — same real synthesis as
        `maybe_digest_conversation()`, refactored to share `_load_convo_and_new_messages()`, but
        digests whatever hasn't been digested yet regardless of count (including a 1-message
        conversation); returns `None` if there's nothing new to digest (an empty conversation)
  - [x] `backend/app/services/chat_conversations.py::delete_conversation()` — attempts the forced
        digest first (best-effort, doesn't block deletion on failure), then deletes the
        conversation row (cascades to its messages via the existing FK), returns an honest
        `{deleted, digested, knowledge_base_id}` — never a fabricated success
  - [x] `DELETE /conversations/{conversation_id}` route
  - [x] Frontend: a delete "×" per tab in `ChatPage.tsx`, with correct active-tab-reassignment
        logic (deleting the currently active tab switches to another remaining conversation, or
        starts fresh if none remain; deleting an inactive tab leaves the active one undisturbed)
  - [x] Real bug found and fixed during this task's own verification, not assumed away: a real
        Voyage 429 rate limit (from cumulative real API usage across this session's extensive
        testing) was hit at `_run_digest()`'s embedding step, discarding an already-synthesized
        real digest entirely — the embedding call is now wrapped in its own try/except
        (`embedding = None` on failure) so a real Claude synthesis is never thrown away over a
        supplementary embedding hiccup, matching the existing documents.py/chat_conversations.py
        null-embedding-then-backfill pattern. Added the missing counterpart for `knowledge_base`
        itself: `agents/knowledge.py::backfill_missing_embeddings()` +
        `POST /admin/knowledge-base/backfill-embeddings` (this exact gap didn't exist before
        because no code path had ever inserted a `knowledge_base` row without embedding it
        synchronously until this task's digest-on-delete flow could).
  - [x] Verified past "no error thrown," including diagnosing three real Playwright-side false
        alarms via direct DB inspection rather than assuming either success or a product bug:
        1. Two clean direct-API tests up front: a real 2-message conversation deleted via curl
           returned `digested:true` with a real, correctly-grounded `knowledge_base` row (content
           verified directly); a real empty conversation deleted via curl returned
           `digested:false` with no junk digest created.
        2. Browser-test attempt 1 used a 15s fixed wait that proved too short given real added
           latency from RAG search + message-embedding calls now in the chat path — it clicked
           before responses settled. Diagnosed via direct DB query showing the deleted
           conversation was NOT the one intended.
        3. Browser-test attempts 1–2 both used Playwright's `.last()` on the tab strip, but
           `list_conversations()` orders `last_message_at DESC` (most-recent-first) — the
           currently active tab is FIRST in DOM order, not last. Both attempts deleted the
           inactive tab instead, confirmed via direct DB inspection each time (not assumed).
        4. A direct re-test of `force_digest_conversation()` against a real leftover conversation
           confirmed the digest mechanism itself was sound under current conditions, ruling out a
           systemic bug before concluding attempts 1–2 were test-script errors.
        5. Browser-test attempt 3 (corrected to `.first()`) raced its own response-capture and
           assertion timing against React's query-invalidation re-render — captured a `null`
           response body and stale tab counts, but a follow-up direct DB check confirmed the real
           delete had, in fact, succeeded correctly server-side.
        6. Browser-test attempt 4, using `Promise.all([waitForResponse, click])` to properly
           synchronize the click and response capture, gave a clean, unambiguous read: tab count
           2→1, deleted tab's content gone, UI correctly reassigned to the remaining tab, zero
           console errors — but surfaced `digested:false` for real, which led directly to
           reproducing and fixing the genuine Voyage-429-discards-the-digest bug described above.
        7. Final direct verification after the fix: deleted a fresh real conversation while Voyage
           was still actively rate-limited — `digested:true` with a real `knowledge_base_id`
           returned, confirmed via direct DB query that `embedding` was correctly `None` (not
           silently discarded), then confirmed `POST /admin/knowledge-base/backfill-embeddings`
           correctly recovered it (`embedded_count:1`, `embedding` now populated).
  - [x] All self-created test conversations, messages, and knowledge_base rows cleaned up from the
        database afterward (across all 7 verification passes above).
