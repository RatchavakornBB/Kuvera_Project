## Result: ✅ DoD met

Gate: `npx tsc --noEmit` ✅ · real browser end-to-end test (Playwright) ✅.

Design decision made and logged before building (see the task file): system-architecture.md
Section 8 calls 4.3 Key-date notifier a "scheduled background check," but this MVP has no task
queue or worker process anywhere, and the 5-day timeline never allocates a build block for one.
Built it as a real on-demand endpoint (`GET /notifications/key-dates`,
`backend/app/services/notifications.py`) instead, polled by the frontend on a 5-minute
`refetchInterval` — functionally equivalent to a scheduled check at this dataset's scale, no new
infrastructure. Only `documents.key_date` feeds it; `milestones.occurred_at` is retrospective (set
once a milestone happens, not a forward-looking due date), so there's nothing there to notify
about — a data-model fact, not an oversight.

This generalizes and effectively supersedes the inline `KeyDatesStrip` computation added in
phase4-002, which only checked documents already loaded on the Documents & Contracts page. The new
`NotificationBell` lives in `TopBar` (`AppShell`), so it's visible on every screen — Dashboard, Deal
Detail, Documents & Contracts, Agent Hub — not just one page.

To exercise this against real data (no document in the seed data had `key_date` set — a known,
already-logged gap from phase4-001a/phase4-002), set a real, plausible key date on Deal A's MSA
contract document: 2026-08-01, the contract's actual 60-day non-renewal notice deadline described
in its own real AI summary from Phase 3 testing. This is a legitimate, deliberate data enrichment
kept in place (not a throwaway artifact), matching the existing worked-example data already seeded
for Deal A.

Verified end to end: badge showed the real count (1) matching the backend response; dropdown listed
the real document/deal/day-count; dismissing the item cleared it from the dropdown and persisted
across a full page reload (confirmed via `localStorage` inspection and via a badge-count check
correctly scoped to the bell — an earlier looser Playwright selector matched an unrelated red badge
elsewhere on the Dashboard, a test-script issue, not an app bug, fixed by scoping to the bell
button). Zero console errors.

Deviations from spec: on-demand/polled rather than a true server-side scheduled job — logged above,
not discovered after the fact.
