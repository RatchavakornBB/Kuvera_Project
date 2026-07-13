## Result: ✅ DoD met

Gate: real WebSocket client (`websockets` library, no mocks), 3 real round trips against the running backend:
1. Message with no `deal_id` → correctly asked "Which deal are you asking about?" instead of guessing or answering ungrounded.
2. Deal-scoped status question → Orchestrator's LLM classifier correctly routed to `concierge_qa`, returned a grounded answer with a well-populated `sources` array (6 named records).
3. Explicit "re-run the document analysis" message → Orchestrator correctly routed to `analyst_lead`, found the deal's most recent document (the contract from phase3-001) via `get_latest_document`, ran the real compiled Analyst Lead graph on it end-to-end, and returned a response with an artifact card.

Deviations from spec: `/chat` is request/response over the WebSocket, not token streaming — D-012, timeline Section 7 cut order item 4, invoked deliberately (Concierge Q&A's structured tool-use output makes true mid-generation streaming meaningfully harder and more failure-prone than this week's clock supports) and logged, not silently dropped.

Risks: `analyst_lead` routing always runs the general Analyst Lead pipeline regardless of what kind of document is latest (in the test, it ran financial-deal analysis over what's actually a contract PDF) — correct per how chat routing is specified (Orchestrator picks between exactly two subgraphs, Concierge Q&A or Analyst Lead; Contracts Lead isn't a chat-routable target this week), but worth knowing this isn't type-aware. The chat message protocol (`{message, deal_id?}` in, `{role, text, sources?, artifact?}` out) isn't yet consumed by the frontend — that's the next task.
