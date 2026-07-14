## Result: ✅ Fixed — a real live hang, root-caused with live evidence rather than assumed

Gate: real hang confirmed via LangGraph checkpoint inspection (not guessed) ✅ · identical call
re-run directly to isolate whether the pipeline itself was broken ✅ · fix re-verified against the
user's own real uploaded document through the live API ✅.

User hit a real, live failure: asking the Chat assistant about an uploaded document left the UI
stuck on "Kuvera Assistant · thinking…" for 5+ minutes with no error. Investigated the actual state
rather than assuming a quick restart would fix it: queried the LangGraph Postgres checkpointer for
the exact `thread_id` that request would have used and found **zero checkpoint rows** — proof the
run never completed even its first node (doc_summarizer), not a slow-but-progressing pipeline.
Then re-ran the identical real call directly (same document, same node function) and it completed
correctly in ~19.5 seconds — ruling out a systemic break in the doc-reading/summarization pipeline
and pointing squarely at a one-off stall in that specific network call.

**Root cause:** `agents/adapters/model_adapter.py::_anthropic_client()` constructed the Anthropic
client with no explicit `timeout` argument, so the SDK's own default (effectively up to ~10
minutes) applied. A stalled TCP connection or hung response can block a FastAPI thread-pool worker
for the full default window with no visible error anywhere — nothing crashes, nothing logs, the
request just never returns. Compounding it: `frontend/src/lib/useChatSocket.ts` had no client-side
timeout either, so even a request that eventually failed server-side (or a response that got lost
in transit) would leave the UI's `busy` flag stuck `true` indefinitely, since it's only ever reset
inside the WebSocket's `onmessage` handler.

**Fixed on both ends, matching this session's pattern of not fixing just the visible symptom:**
- Backend: explicit `timeout=120.0` on the Anthropic client. A stall now raises a real exception
  within a bounded time, which `with_retry` (already correctly implemented — 2 bounded attempts,
  converts to `NodeFailure`) turns into a clean, surfaced error instead of an invisible hang.
- Frontend: a 150-second client-side timer starts on every `send()`, comfortably longer than the
  new backend ceiling plus round-trip/retry overhead. If no response arrives in time, `busy`
  resets and the user gets a real message telling them the request stalled, instead of staring at
  an indefinite "thinking…" with no way to know whether to wait longer or give up.

**Re-verified against the user's own real data, not synthetic test data**, after restarting the
backend with the fix live: re-ran the actual `/analyze` call against their real uploaded document
(`Kuvera_Capital_AI_Platform_System_Design (3).docx` in their real "CP All" deal) through the live
API and got a clean 200 with a correct, grounded response. This document was left untouched
afterward — it's the user's own real data from their own testing, not a self-created artifact to
clean up.

No open deviations. The user needs to refresh their browser tab once to reconnect the WebSocket,
since restarting the backend closed the prior connection server-side — communicated this to them
directly.
