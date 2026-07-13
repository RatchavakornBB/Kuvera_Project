Scope: backend/app/services/notifications.py, backend/app/routes/notifications.py,
backend/app/main.py, frontend/src/lib/api.ts,
frontend/src/components/layout/NotificationBell.tsx, frontend/src/components/layout/TopBar.tsx,
frontend/src/components/layout/AppShell.tsx
Depends on: phase4-003 (done)
Files allowed to touch: files listed above

Design decision (log before building): system-architecture.md Section 8 describes 4.3 Key-date
notifier as a "scheduled background check" — this MVP has no task-queue/cron infrastructure
(no Celery/APScheduler, no worker process), and adding one just for this single feature would be
disproportionate to a 5-day build (the 5day-build-timeline.md doesn't allocate a build block for
a scheduler anywhere). Implementing this as an on-demand check instead: a real GET endpoint that
computes upcoming/overdue key dates fresh on every call, invoked by the frontend on mount and on a
client-side polling interval (TanStack Query `refetchInterval`) — functionally equivalent to a
frequent server cron at this dataset's scale, without new infrastructure. This generalizes and
replaces the ad-hoc KeyDatesStrip logic added inline in phase4-002 (Documents & Contracts screen),
which only checked documents already loaded on that one page.

DoD:
  - [x] GET /notifications/key-dates?days=30 — real cross-deal, cross-document check (not
        page-scoped like phase4-002's strip), joined with deal name
  - [x] Persistent NotificationBell in TopBar (visible on every page, not just Documents &
        Contracts): badge count, dropdown listing items sorted soonest-first, click navigates to
        the owning deal
  - [x] Dismiss-per-item, not per-session (ux-ui-spec.md Section 3.4's notifications strip
        requirement) — persisted in localStorage since there's no backend audit/dismiss table for
        this in the MVP schema
  - [x] Verified end to end in a real browser: bell shows the real badge count matching backend
        data, dropdown lists real key dates, dismissing one removes it and persists across a page
        reload, clicking an item navigates to the real deal, zero console errors
