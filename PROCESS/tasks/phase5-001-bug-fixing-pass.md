Scope: verification-first — fix whatever real bugs are found. Likely touches: frontend empty-state
components (already mostly built in Phase 4, checking they handle sparse real data), any backend
edge case surfaced by testing against Horizon Freight Corp / Nova Fintech (sparse seed data).
Depends on: Phase 4 complete (done)
Files allowed to touch: whatever bugs are actually found — no speculative refactors.

DoD:
  - [x] Click through Horizon Freight Corp and Nova Fintech (sparse real data, no fabricated
        fixtures) across every screen: Dashboard views, Deal Detail all 4 tabs, Documents &
        Contracts, Agent Hub — confirms empty states render correctly, not just Deal A's
        data-rich path
  - [x] NewDealModal validation edge cases (empty name/client, whitespace-only input)
  - [x] Console warnings (not just errors) checked across every screen — React key warnings,
        missing dependency arrays, accessibility warnings
  - [x] Grep for leftover TODO/FIXME/debug console.log statements across frontend + backend +
        agents
  - [x] Any real bug found is fixed, verified with real execution (not just typecheck), and
        logged in the report — this task does not touch working code without a proven bug
