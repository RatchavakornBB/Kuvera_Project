Scope: agents/adapters/model_adapter.py, frontend/src/lib/useChatSocket.ts
Depends on: none — a robustness fix triggered by a real live failure the user hit

Scope: user reported a real, live hang: asking the Chat assistant about a document (over the
actual WebSocket, in their own browser session) left the UI stuck on "Kuvera Assistant ·
thinking…" for 5+ minutes with no error and no response. Investigated live rather than guessing:
checked the LangGraph Postgres checkpointer for that exact thread_id and found zero checkpoint
rows — the run never even completed its first node — then re-ran the identical real call directly
(same document, same node) and it completed cleanly in ~19.5 seconds, proving the underlying
capability wasn't broken. Root cause: `agents/adapters/model_adapter.py::_anthropic_client()`
constructed the Anthropic client with no explicit `timeout`, so the SDK's own generous default
(effectively up to ~10 minutes) meant a stalled network call could block a FastAPI thread-pool
worker indefinitely with zero visible error — and even once resolved server-side, the frontend
(`useChatSocket.ts`) had no client-side timeout either, so a lost/stuck response would leave
`busy: true` forever with no recovery short of a manual page refresh.

DoD:
  - [x] `agents/adapters/model_adapter.py`: `_anthropic_client()` now passes an explicit
        `timeout=REQUEST_TIMEOUT_SECONDS` (120.0) to the Anthropic client constructor — a stall now
        surfaces as a real exception, which `with_retry` (agents/retry.py, unchanged, already
        bounded at 2 attempts) converts into a clean `NodeFailure` instead of hanging silently
  - [x] `frontend/src/lib/useChatSocket.ts`: `send()` now starts a 150-second client-side timer
        (comfortably longer than the backend's 120s limit plus retry/network overhead); if no
        `onmessage` arrives before it fires, `busy` resets and a real assistant-role message tells
        the user the request stalled and to retry or refresh — the timer is cleared on both a real
        response arriving and on unmount, so it never fires spuriously after a normal reply
  - [x] Verified past "no error thrown, assumed fixed": (1) confirmed the underlying live hang was
        real by checking the LangGraph checkpoint table for the exact thread_id and finding zero
        rows — proof the graph never progressed past its entry point, not a slow-but-progressing
        run; (2) re-ran the identical real call (same PDF, same node, doc_summarizer) directly and
        it completed correctly in ~19.5s, ruling out a systemic breakage in the underlying pipeline
        and confirming the hang was a one-off network stall, exactly the failure mode the missing
        timeout would allow; (3) after applying the fix and restarting the backend, re-ran the
        real `/analyze` call against the user's own actual uploaded document
        (Kuvera_Capital_AI_Platform_System_Design (3).docx, deal "CP All" — real user data, left
        untouched, not cleaned up) through the live API and confirmed a clean 200 with a real,
        correct, grounded response
  - [x] `tsc --noEmit` clean, Python import check clean
