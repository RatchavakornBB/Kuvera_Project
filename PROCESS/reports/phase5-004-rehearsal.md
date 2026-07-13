## Result: ✅ Demo script verified real, timing confirmed comfortable

Ran the entire `docs/demo-script.md` click path (steps 1–13) as a real, timed Playwright session
against the live backend/frontend/Supabase stack — every selector in the script actually exists and
works; nothing in the written script is aspirational.

**Timing** (mechanical/app time only, excludes narration): total 9.5 seconds across all 13 steps —
Dashboard load 1.4s, view-toggle switches ~0.3–0.7s each, Deal Detail navigation 0.6s, real file
upload 1.7s, Analysis tab (pre-computed, no live LLM call) 1.1s, real add-task round trip 1.7s,
chat panel open 0.1s, Documents & Contracts + search 0.8s, Agent Hub 0.4s. This confirms the app
itself is not a bottleneck — the script's 10–12 minute estimate is entirely narration-paced, which
is the intended shape for an interview demo. Zero console errors during the run.

Per the demo script's own advice, the rehearsal did **not** trigger a live Analysis-tab Regenerate
(that real LangGraph run takes ~2–3 minutes) — it only confirmed the tab renders the real
pre-computed results, matching exactly what a live presenter should do.

**Cleanup, and a process note worth keeping:** the rehearsal run itself created real test
artifacts in Deal A's data (2 throwaway tasks named "Rehearsal check <timestamp>", 2 duplicate
`deal_a_financial_summary.pdf` uploads) — since there's no DELETE endpoint for tasks/documents in
this MVP, cleanup meant writing directly against Supabase rather than through the app's own API.
Deleted the 2 tasks first (their names contained a script-generated timestamp, unambiguously
self-created), which triggered a Claude Code auto-mode permission denial on a subsequent read
query — the classifier flagged that a raw DB delete against records "not named by the user" is an
irreversible action that should be reviewed, even though the specific rows were clearly identifiable
as this session's own artifacts. Stopped, explained the situation, and got explicit user
confirmation before deleting the 2 duplicate document uploads (also Storage + DB row, matching the
same compensating-cleanup pattern `upload_document()` already uses on its own failure path).
Confirmed via a fresh `GET /deals/{id}` that Deal A's task list is back to its intended 2 real
entries.

Deviations from spec: none — this was a verification-only task by design.
