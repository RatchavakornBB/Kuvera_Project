Scope: backend/app/routes/deals.py, backend/app/services/deals.py,
frontend/src/lib/api.ts, frontend/src/components/dealDetail/TaskList.tsx,
frontend/src/components/dealDetail/MeetingNotesFeed.tsx, frontend/src/pages/DealDetail.tsx
Depends on: phase4-001c (done)
Files allowed to touch: files listed above
DoD:
  - [x] POST /deals/{id}/tasks and PATCH /deals/{id}/tasks/{task_id} — matches the
        5day-build-timeline.md API table's explicit `/deals/{id}/tasks` POST/PATCH entry
  - [x] Pending task list with owner/due date, quick-add input, checkbox to mark done
        (ux-ui-spec.md Section 3.2: "Pending task list with owner/due date")
  - [x] Meeting notes feed, chronological (most recent first), showing attendees + the
        real AI-generated summary per entry
  - [x] Verified end to end in a real browser: added a real task via the input, watched it
        appear immediately (query invalidation, not manual refresh), toggled it done and
        watched it move into a "Done" section, zero console errors
