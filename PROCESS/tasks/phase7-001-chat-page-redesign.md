Scope: frontend/src/App.tsx, frontend/src/components/layout/AppShell.tsx,
frontend/src/components/layout/TopBar.tsx, frontend/src/components/layout/Sidebar.tsx,
frontend/src/components/chat/ChatComposer.tsx, frontend/src/pages/ChatPage.tsx (new),
frontend/src/pages/Today.tsx (new), frontend/src/pages/DailyDigest.tsx (new),
frontend/src/components/chat/ChatPanel.tsx (removed — superseded)
Depends on: existing useChatSocket/agents.orchestrator (Phase 3), fetchDeals/fetchKeyDateNotifications
(Phase 1/4), Learning Agent digests (phase6-003)

Scope: user reported "the Chat page doesn't exist" and provided a reference screenshot of a
NotebookLM-style full-page Chat interface (Sources panel with the portfolio's deals, mode tabs,
message thread) that doesn't match ux-ui-spec.md Section 3.3's written spec (a slide-out panel).
Clarified scope with the user before building, since the mockup's "Sources" list showed the whole
7-deal portfolio selectable at once, which conflicts with a structural invariant this app has
enforced everywhere: every AI answer is scoped to exactly one deal
(agents/deal_context.py — "no deal_id means no answer"). User confirmed: single-deal selection only
(not real multi-deal chat), the 4 mode tabs are cosmetic (no backend routing change — the
Orchestrator still does real intent classification on every message regardless of tab), and to
build the rest of the mockup too (Today page, Daily Digest page, "View as: Owner" badge).

DoD:
  - [x] `/chat` is now a real routed page (ChatPage.tsx), not a toggled side panel — supersedes
        ux-ui-spec.md 3.3's "slide-out" framing per the user's explicit newer direction
  - [x] Sources panel: real `fetchDeals()` data, single-select (clicking a deal sets it as the
        active chat context, matching the existing `dealContextLabel`/`onClearContext` composer
        pattern that already existed) — NOT true multi-select, per the user's explicit choice to
        keep the single-deal-scope invariant intact
  - [x] 4 mode tabs (Concierge/Analyst/Contracts/Drafting): cosmetic only — change the composer
        placeholder and accent color, do NOT change which backend logic handles the message; the
        real Orchestrator (`agents/nodes/orchestrator.py::classify_intent`) still makes the actual
        routing decision on every send, unconditionally
  - [x] `useChatSocket()` stays instantiated in AppShell (not moved into ChatPage) so message
        history persists across navigation — preserves the one part of the original spec's
        "persists across navigation" intent that's still true
  - [x] `askAboutDeal()` (used by Deal Detail's "Ask about this deal" panel) now sets the selected
        deal and navigates to `/chat` instead of toggling a panel — verified this still correctly
        pre-selects the deal as the active Source
  - [x] `/today`: real needs-attention deals (reuses the exact filter `NeedsAttentionRail` already
        used) + real upcoming key dates (`fetchKeyDateNotifications`) — no new backend endpoint
        needed, no fabricated data
  - [x] `/daily-digest`: wraps the existing, already-real `LearningAgentTab` component (built in
        phase6-003) with a page header — same real digest data and research-cycle trigger, just
        promoted from an Admin sub-tab to its own nav item
  - [x] "View as: Owner" badge: added as a static, honestly-labeled, non-interactive badge with a
        tooltip explaining role-switching isn't built — there is no real RBAC/multi-user backend in
        this app (documented as "Not built" in demo-script.md), and building fake role-switching
        logic just to match a screenshot would be fabrication; the badge reflects the one real role
        that exists rather than pretending to offer a choice that doesn't
  - [x] Sidebar reordered to match the reference: Today, Dashboard, Chat, Documents & Contracts,
        Daily Digest, Agent Hub, Admin. Deliberately did NOT add a separate "Deals" nav item next
        to "Dashboard" — the existing Dashboard page already IS the deals list (Board/Table/
        Pipeline views, `<h1>Deals</h1>`); adding a second nav item pointing at near-identical
        content would be a dishonest duplicate, not a real feature
  - [x] Removed `ChatPanel.tsx` (the old slide-out panel component) — dead code once nothing
        referenced it after the AppShell rewrite
  - [x] `ChatComposer.tsx` gained an optional `placeholder` prop (used by the mode tabs) —
        backward-compatible, defaults to the original text
  - [x] Verified past "no error thrown": `tsc --noEmit` clean across the whole frontend after every
        edit; real browser walkthrough covering all of: Today page real data, Sidebar nav order,
        Chat page Sources panel + tab colors, selecting a Source and sending a REAL message over
        the real WebSocket — the response correctly demonstrated the deal_id scoping invariant
        still holding ("I don't have visibility into a portfolio of multiple deals — my knowledge
        is scoped to exactly one deal: 'Deal A'..."), Daily Digest showing real prior digest data,
        "Ask about this deal" from Deal Detail correctly navigating to /chat with the deal
        pre-selected, and no regressions in Dashboard/Documents & Contracts/Agent Hub/Admin (all
        share the rewritten AppShell/TopBar/Sidebar) — zero console errors across every screen
