Scope: agents/deal_context.py, agents/nodes/concierge_qa.py, backend/app/routes/chat.py (Q&A portion only — WebSocket is phase3-004), backend/app/services/concierge.py
Depends on: phase2-* (deal/document/analysis data now exists to answer questions about)
Files allowed to touch: files listed above
DoD:
  - [x] deal_id scoping enforced structurally (only that deal's rows are ever fetched/included in the prompt context), not just an instruction the model could ignore — this is AGENT.md's one invariant treated as seriously as a money/auth bug (Section 11)
  - [x] "Lightweight RAG" = direct context-stuffing (gather all of one deal's data into the prompt), not real vector search — logged as D-011, since the data scale (a handful of records per deal) makes pgvector infrastructure premature this week
  - [x] Grounded answer + structured sources list naming which records were used
  - [x] Verified: asking about Deal A's real status/documents/risks returned a correct, well-grounded answer pulling from deal fields, milestones, documents, DD checklist, meeting notes, tasks, AND the contract clauses uploaded in phase3-001. Same question scoped to Horizon Freight Corp returned a completely different, correctly-scoped answer with zero Deal A leakage (checked programmatically) — and, since that deal has minimal seeded data, correctly said it didn't have enough grounded information rather than fabricating risks.
