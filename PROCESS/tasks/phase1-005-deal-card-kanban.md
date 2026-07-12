Scope: frontend/src/lib/, frontend/src/components/DealCard.tsx, frontend/src/components/KanbanBoard.tsx, frontend/src/data/mockDeals.ts, frontend/src/App.tsx (verification harness)
Depends on: phase1-001-design-tokens-stage-diagram (done — StageDiagram, design tokens)
Files allowed to touch: files listed above only
DoD:
  - [x] Deal card shows name, client, owner avatar, risk-flag count badge, compact StageDiagram, status label — per ux-ui-spec.md Section 3.1 and the Board view section of docs/mockups/Kuvera Capital.dc.html
  - [x] Kanban column shell: one column per M&A stage, deals grouped correctly
  - [x] A single hardcoded deal card renders with correct styling (Phase 1 timeline checkpoint)
  - [x] Restricted/RBAC card variant explicitly NOT built — RBAC is Phase 3 design-only scope per system-architecture.md Section 1.4
  - [x] npx tsc --noEmit passes
  - [x] Rendered in a real browser, zero console errors
