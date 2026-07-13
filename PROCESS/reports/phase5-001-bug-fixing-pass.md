## Result: ✅ One real bug found and fixed; everything else confirmed benign

Gate: real browser testing (Playwright) against real sparse data (Horizon Freight Corp, Nova
Fintech — zero contacts/documents/tasks/meeting_notes/dd_items/milestones), a real production
build (`npm run build` + `vite preview`), and backend log inspection.

**Real bug found and fixed:** `frontend/src/index.css` had the Google Fonts `@import` listed after
`@import 'tailwindcss'`, which violates the CSS spec (`@import` rules must precede all other rules)
— Lightning CSS flagged it during every production build. Fixed by reordering the font import
first. Rebuilt and confirmed the warning is gone, and confirmed via `getComputedStyle` that `Inter`
still resolves correctly as the body font (the fix didn't break font loading).

**Investigated, confirmed NOT bugs (with real verification, not assumption):**
1. `net::ERR_ABORTED` on `/deals/{id}/analysis` during a fast test run — an in-flight fetch
   cancelled by TanStack Query when a test script navigated away before it resolved; confirmed via
   direct `curl` that the endpoint itself returns 200 cleanly.
2. `WebSocket connection... closed before the connection is established` — reproduced only in dev
   mode (`npm run dev`), never in a production build (`vite build` + `vite preview`, verified with
   zero console warnings on prod). Root cause: React 18 `StrictMode` (enabled in `main.tsx`)
   intentionally double-invokes effects on mount in dev only, so `useChatSocket`'s WebSocket opens,
   immediately closes, then reopens — cosmetic dev-only noise, not a real reconnect bug. Confirmed
   `useChatSocket`'s WebSocket lives in `AppShell`, which never unmounts across client-side route
   changes (only the routed `<Outlet>` content changes), so it only opens once per real session.
3. `ConnectionResetError: [WinError 10054]` in the backend log — a well-known cosmetic artifact of
   Python's asyncio `ProactorEventLoop` on Windows when a WebSocket client disconnects abruptly
   (browser tab closed, or StrictMode's rapid dev-mode double-connect). Confirmed the server kept
   handling subsequent requests correctly afterward (log shows successful 200s right after) — no
   crash, no functional impact. Not fixed: this is an upstream Windows/asyncio limitation, not
   application logic, and "fixing" it would mean adding exception-suppression machinery for a
   cosmetic dev/Windows-only log line — logged here so it isn't mistaken for something worse if
   seen on a demo machine's console.
4. All empty states (Overview/Documents/Analysis/Tasks & Notes tabs, NewDealModal validation)
   confirmed rendering correctly against real sparse data — Horizon Freight Corp and Nova Fintech
   have zero rows in every child table, exercising every "No X yet" empty-state branch built across
   Phase 4 simultaneously. Nothing crashed, nothing showed a raw error or blank screen.
5. No leftover `TODO`/`FIXME`/debug `console.log`/`print()` statements anywhere in
   `frontend/src`, `backend/app`, or `agents`.

**Reconfirmed, not re-investigated (already logged in the Phase 1 backlog as accepted polish, not a
bug):** the Kanban board's horizontal tightness at default viewport width — visible again in this
pass's screenshots (Deal A and Nova Fintech's columns cut off). This is the next item, addressed in
phase5-002 (visual polish).
