## Result: ✅ DoD met

Gate: `npx tsc --noEmit` ✅ · real browser end-to-end test (Playwright) ✅.

New backend surface, matching the timeline's API table exactly: `POST /deals/{id}/tasks` and
`PATCH /deals/{id}/tasks/{task_id}` (`app/routes/deals.py`, `app/services/deals.py`). Frontend
`TaskList` renders pending tasks with due date, a quick-add form wired to the real POST endpoint,
and a checkbox per task wired to the real PATCH endpoint to toggle `done`; completed tasks move
into a collapsed "Done" section. `MeetingNotesFeed` renders `deal.meeting_notes` chronologically
(newest first) with attendees and the stored AI summary per entry — read-only, matching spec (no
meeting-note authoring flow was requested for this tab).

Verified against Deal A's real data: added a real task ("Confirm audited FY2025 financials with
CFO"), watched it appear immediately via TanStack Query cache invalidation, checked it done, and
confirmed it moved into the Done section with strikethrough styling — all against the real
Supabase-backed endpoint, zero console errors.

Deviations from spec: none.

Risks: the test task added during verification was left in Deal A's seed data (marked done) rather
than deleted, since no DELETE /tasks endpoint exists (not requested by spec) and the task itself is
a plausible, harmless diligence item — same precedent as phase4-001b's leftover test upload.
