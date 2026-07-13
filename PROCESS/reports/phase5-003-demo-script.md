## Result: ✅ DoD met

Wrote `docs/demo-script.md`: a one-sentence framing, a pre-demo checklist, a 13-step click path
(~10–12 minutes) with a talk track for each step, an explicit Live vs. Design-only table, rehearsed
one-liners for the likely "what about X" questions, and a fallback plan.

Every fact in the script was verified against the real running app immediately before writing, not
recalled from memory or assumed from the design docs:
- Pulled Deal A's real risk-flag count (7), docs-pending count (4), and the real notification badge
  state (1 upcoming key date, 19 days out) via `curl` against the live backend.
- Confirmed Drafting Lead (5.1/5.2), Knowledge Agent, and Learning Agent were never built by
  listing `agents/nodes/` directly (only doc_summarizer, risk_flagger, ic_memo_drafter,
  pricing_advisor, contract_summarizer, clause_extractor, concierge_qa, orchestrator, web_research
  exist).
- Confirmed there is no login/auth UI anywhere in `frontend/src` (grepped for
  `login|Login|signIn|auth`, zero matches) before writing the RBAC answer.
- Cross-checked the Agent Hub's real scope (static log, not the full 21-agent grid) against
  phase4-003's report rather than re-describing it from memory.

One practical risk flagged prominently in the script itself: a live `/analyze` regenerate run takes
~2–3 minutes (4 real sequential/parallel Claude API calls), which is too slow to sit through live in
an interview — the script explicitly tells the presenter to show the already-computed real results
instead and only mention regeneration is one click away, rather than accidentally stalling the demo.

Considered and deliberately decided against: deleting the leftover duplicate
`deal_a_customer_msa.pdf` test-upload document from earlier Phase 4 QA testing to "clean up" the
demo data. It's referenced by real `analyses` rows (foreign key, no `ON DELETE CASCADE`) that back
the Agent Hub's historical trace — deleting it would either fail on the FK constraint or, if forced,
silently degrade the Agent Hub demo's document-name lookups. The cosmetic gain (avoiding a
duplicate filename) wasn't worth that risk; the script instead prepares an honest one-line
explanation if asked.
