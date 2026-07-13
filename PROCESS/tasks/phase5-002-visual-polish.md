Scope: frontend/src/components/KanbanBoard.tsx (the one concretely logged backlog item);
verification pass over loading-state consistency across the app (no changes needed there).
Depends on: phase5-001 (done)
Files allowed to touch: KanbanBoard.tsx, plus anything else a real check surfaces.

DoD:
  - [x] Kanban board horizontal-scroll affordance (backlog item logged in Phase 1's phase1-007
        report): a fade hint on whichever edge(s) have more content to scroll to, real scroll
        position tracked via a ref + scroll/resize listener, not a static always-on decoration
  - [x] Verified in a real browser at the same 1280px viewport where the tightness was originally
        observed: fade appears only on the correct edge at each scroll position (none at scrollLeft
        0 on the left, right fade at start, left fade after scrolling to the end)
  - [x] Loading-state text pattern checked for consistency across all 5 pages that fetch data —
        confirmed already consistent ("Loading X…", text-gray, no changes needed)
