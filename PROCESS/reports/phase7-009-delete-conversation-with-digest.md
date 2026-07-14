## Result: ✅ DoD met — delete-with-forced-digest works correctly, plus a real bug found and fixed that would have silently discarded synthesized digests under rate-limit pressure

Gate: two clean direct-API tests establishing baseline correctness ✅ · four browser-test attempts,
three producing real false alarms diagnosed via direct DB inspection (not assumed) rather than
Playwright script bugs going unnoticed ✅ · a genuine product bug found via that diagnosis process
and fixed ✅ · final verification confirming the fix under a real active rate limit ✅.

User asked for tabs to be deletable, with the system summarizing the conversation into memory
first. This reused phase7-008's existing digest machinery rather than inventing a second
summarization path: `force_digest_conversation()` runs the same real Claude synthesis as the
automatic every-10-messages digest, just bypassing that count threshold so a short conversation
isn't lost to a premature close. `delete_conversation()` attempts this digest, then deletes
regardless of whether it succeeded (best-effort — never traps the user with an undeletable tab),
returning an honest `{deleted, digested, knowledge_base_id}`.

**Verification took real effort to get right, and that effort surfaced a genuine bug.** Two direct
API tests established the mechanism was sound in isolation. Browser testing then hit four rounds of
what looked like failures, three of which turned out to be Playwright-side issues (a too-short
fixed wait given real added chat latency from RAG search; `.last()` selecting the wrong tab because
`list_conversations()` orders most-recent-first, not last; a response-capture race against React's
own re-render) — each diagnosed by checking the real database directly rather than trusting or
distrusting the test output at face value. That discipline mattered: attempt 4, once properly
synchronized, gave a clean UI confirmation (tab count, content removal, active-tab reassignment,
zero console errors) but still reported a real `digested:false`.

Reproducing that directly (bypassing the best-effort exception swallow) found a genuine bug:
`_run_digest()` computed the real Claude synthesis successfully, then discarded the *entire* digest
— synthesized content and all — when the immediately-following embedding call hit a real Voyage 429
(a rate limit legitimately earned from this session's own extensive real API testing). This is
strictly worse than the null-embedding-then-backfill pattern already established elsewhere in this
codebase for exactly this failure class (`documents.py`, `chat_conversations.py`) — here, a
genuinely good, already-computed synthesis was being thrown away over a supplementary step.

**Fixed by decoupling creation from embedding**: the embedding call is now its own try/except
(`embedding = None` on failure), so the `knowledge_base` row is still inserted with its real
content regardless. This exposed a related gap: no backfill existed for `knowledge_base` itself
(every prior code path had always embedded synchronously and successfully, or failed the whole
write) — added `agents/knowledge.py::backfill_missing_embeddings()` and
`POST /admin/knowledge-base/backfill-embeddings`, the same batched-catch-up pattern already used for
documents and chat messages.

**Final verification confirmed the fix directly under live rate-limit conditions**: deleted a fresh
conversation while Voyage was still actively returning 429s — got back `digested:true` with a real
`knowledge_base_id`, confirmed via direct query that `embedding` was correctly `None` rather than
the row being missing entirely, then confirmed the new backfill endpoint recovered it cleanly
(`embedded_count:1`).

All self-created test data across every verification pass — seven in total, counting the diagnostic
detours — was cleaned up from the database afterward. No open deviations.
