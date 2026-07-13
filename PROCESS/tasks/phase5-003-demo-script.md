Scope: docs/demo-script.md (new)
Depends on: phase5-001, phase5-002 (done)
Files allowed to touch: docs/demo-script.md

DoD:
  - [x] Exact click path with a talk track, verified against the real running app's current real
        data (not assumed from the design docs) — deal names, risk-flag counts, key-date
        countdown, document names all pulled fresh via curl before writing
  - [x] Explicit Live vs. Design-only table covering every screen and every likely "what about X"
        gap (RBAC, Skill governance, Drafting Lead, Knowledge/Learning Agent, pgvector, cron,
        cloud deploy) — cross-checked against the actual agents/nodes/ directory and frontend
        routes, not just recalled from memory
  - [x] Rehearsed one-line answers for anticipated questions, written to be honest about gaps
        rather than deflecting
  - [x] A fallback plan for live-demo failure (restart order, "show a saved version instead of
        debugging live", how to handle an off-script question)
