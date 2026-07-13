Scope: verification only (5day-build-timeline.md's final Phase 4 block, 16:00-17:30:
"Full integration pass: Dashboard -> Deal Detail -> Chat as one uninterrupted flow, fix any
broken links/state between screens")
Depends on: phase4-001 through phase4-004 (all done)
Files allowed to touch: whatever breakage is found (none was)
DoD:
  - [x] One continuous real-browser session (not isolated per-page loads): Dashboard (Board/Table/
        Pipeline view switches) -> click into Deal A -> all 4 Deal Detail tabs -> Ask Kuvera
        Assistant (deal-scoped chat) -> Documents & Contracts (sidebar nav) -> Agent Hub (sidebar
        nav) -> back to Deal Detail (via an Agent Hub row's deal link) -> back to Dashboard
        (sidebar nav)
  - [x] Cross-page state persistence verified: Chat panel stays open with "Scoped to Deal A"
        across navigation (AppShell owns chat state, outside the routed Outlet, by design); the
        NotificationBell badge persists across every screen
  - [x] Zero console errors, zero failed requests, across the entire session
