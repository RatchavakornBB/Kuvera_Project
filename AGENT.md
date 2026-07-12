# AGENT.md — KUVERA CAPITAL (AI Deal-Ops Platform)

Operational guide for the Claude Code agent working in this repo (VS Code extension).
Read this file **every session, before touching anything else**. It tells you **how to
work here**; the **what to build** lives in `docs/system-architecture.md`,
`docs/ux-ui-spec.md`, and `docs/5day-build-timeline.md`. This is a **5-day MVP build**
against a hard interview/demo deadline — the timeline's Phase 1–5 schedule and its
Section 7 cut order are load-bearing, not background info.

> **Place this file at the repo root.** Point every task at the relevant phase section
> of `docs/5day-build-timeline.md` — never try to build the full 21-agent architecture
> at once.

---

## 0. The six failure modes this file exists to prevent

Every section below maps back to one of these. When in doubt about *why* a rule exists,
it's one of these six:

1. **Silently breaking working code** while "improving" something nearby.
2. **Losing context across sessions/context resets** and guessing the wrong state
   instead of checking it.
3. **Editing or reporting on files without actually reading their current content
   first** — acting on a remembered or assumed version instead of what's on disk.
4. **Calling something "done" without verifying it actually runs error-free** —
   endpoints, LangGraph nodes, and UI screens must be exercised, not just written.
5. **Working open-ended instead of as a closed, resumable loop** — task in, verify,
   report, checkpoint, next.
6. **A sub-agent/LangGraph node timing out, failing, or looping without anyone
   noticing** — failures must be caught, diagnosed, logged, and surfaced to the user,
   never left to fail silently or retry forever.

---

## 1. Environment & stack (read before running commands)

- **Repo layout:** `/frontend` (React 18 + Vite + TanStack Query + Tailwind), `/backend`
  (FastAPI), `/supabase` (CLI-managed migrations + seed), `/agents` (LangGraph graph +
  node definitions).
- **Local-first by design.** Supabase runs locally via Docker (`supabase init &&
  supabase start`) — full Postgres/Auth/Storage/pgvector parity with the cloud product.
  Cloud deploy is an optional Phase 5 step, never a dependency for dev or demo.
- **Secrets:** `.env`, gitignored. `ANTHROPIC_API_KEY` is required; `OPENAI_API_KEY` /
  `GOOGLE_API_KEY` / `DEEPGRAM_API_KEY` are optional. A single `config.py` /
  `config.ts` **validates required keys at startup and fails fast, naming the missing
  key** — never let a missing key surface as a silent mid-request failure during a demo.
- **Model calls go through one adapter, never the SDK directly.** Every LangGraph node
  calls `call_model(agent_name, messages, tools=[])`, which looks up `agent_name`'s
  `model_id` from config and dispatches to the right client. This is what makes adding
  OpenAI/Gemini later a config change, not a rewrite — do not let a node call
  `anthropic.Anthropic()` directly, even "just for now."
- **Checkpointer:** Supabase Postgres, from day one — the same mechanism specified for
  production. Do not swap in an in-memory checkpointer "to move faster"; it changes
  session-recovery behavior (Section 4 below) and would need re-architecting later.

---

## 2. Commands / gate

Run before saying any task is done. If a script isn't wired up yet, add it to the right
`package.json` / `pyproject.toml` rather than inventing an ad-hoc command.

```bash
# Frontend
npm install
npm run dev
npm run typecheck        # tsc --noEmit
npm run lint
npm run test             # vitest

# Backend
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest                              # all backend tests
pytest tests/agents/                # LangGraph node tests only

# Supabase (local)
supabase start
supabase stop
supabase migration new <name>
supabase db reset                   # rebuild local DB from migrations + seed
supabase status                     # confirm Postgres/Auth/Storage/Realtime all up
```

**Before marking any task done, run:** `npm run typecheck && npm run lint && npm run
test` **and** `pytest` (and `supabase db reset` if you touched schema/seed). This
mirrors the CI gate and is non-negotiable — see Section 8 (Definition of "done").

---

## 3. Golden rule — verify, then leave working code alone

> When a task or phase checkpoint (see the Phase timeline in `docs/5day-build-timeline.md`
> Section 6) is finished, **check that it's correct**, then **do not modify that code
> again** — not to "clean it up," refactor, or restyle. **Touch already-working code
> only when there is a confirmed bug**, and change the smallest amount needed to fix it.

**Worked example.** `agents/nodes/doc_summarizer.py` (node 3.1) is finished and its test
passes:

```python
def doc_summarizer(state: AnalystState) -> AnalystState:
    summary = call_model("doc_summarizer", build_summary_prompt(state["document_text"]))
    return {**state, "summary": summary}
```

Later, while building node 3.2 (`risk_flagger`), you notice 3.1 doesn't truncate very
long documents and think "I'm in here anyway, let me add truncation."

✗ **Don't.** That's an unrequested change to a finished, tested node — if it changes
what gets summarized, every downstream node (risk_flagger, ic_memo_drafter) that trusts
`summary` now sees different input, and nothing in the test suite will catch it because
the golden tests for 3.2/3.3 were written against the old summary shape.

✓ **Do.** Log it to `PROCESS/backlog.md` as a deferred finding, and only touch
`doc_summarizer.py` if truncation is itself the active task, following the Debugging
Protocol (Section 9) with a failing test first.

**Exception — a real, confirmed bug** (e.g. `doc_summarizer` crashes on a specific
document type): (1) write a failing test reproducing it, (2) make the smallest change
that turns it green, (3) run the full gate, (4) stop — no adjacent cleanup.

---

## 4. Session continuity — verify state before continuing, never assume

Claude Code sessions in this repo don't reliably run start-to-finish — a 5-day sprint
means many short sessions. A new session has **no memory of the last one**, only what's
on disk, in git, and in the local Supabase instance. Before touching anything:

```bash
git status                     # uncommitted/staged changes left by a prior session?
git log --oneline -10          # what actually landed, vs what a chat/PR claims landed
git diff HEAD~1                # if the last commit looks WIP, see what's actually in it
supabase status                # is local Supabase even running?
supabase migration list        # each migration: applied locally or not?
supabase db diff               # drift between local DB and migration files on disk
curl localhost:8000/deals      # does the backend actually respond, right now?
```

**Do not assume:**
- `git status` is clean because a previous message said "done" — check yourself.
- every file in `supabase/migrations/` has been **applied** — a file existing means
  someone wrote it, not that `supabase db reset` ran afterward.
- a phase checkpoint marked complete in a stale chat/PR description is still accurate —
  re-run the gate (Section 2) and hit the actual endpoint/screen yourself.
- Docker/Supabase is running just because it was running last session — `docker ps` /
  `supabase status` first, every session; a large share of "mystery bugs" in a
  local-Docker setup are just the stack not being up.
- uncommitted changes on disk are safe to discard. If `git status` shows dirty files you
  didn't just create, **stop and ask** — it may be unfinished prior-session work, not junk.

If disk/DB state and the last known-good commit disagree, **disk state is ground
truth** — but surface what you found (uncommitted diff, un-applied migration, a
checkpoint claim that doesn't hold up) before building on top of it.

---

## 5. File reading discipline — never act on a remembered or assumed file

This is its own rule because it's the single easiest way to silently corrupt a repo:

- **Before editing any file, `view` it — even a file you edited five minutes ago in
  this same session.** Context can be summarized or trimmed; treat your own memory of a
  file's contents as unverified until you've re-read it.
- **Before writing code that depends on another file's shape** (a Pydantic model, a
  Supabase table schema, a TypeScript interface, a LangGraph state type), open and read
  that file — don't infer its shape from the filename, from what it "should" contain per
  the spec, or from an earlier conversation about it. The spec describes intent; the
  file on disk is truth.
- **Before claiming a file doesn't exist or doesn't contain something, search/grep for
  it.** Don't report "there's no error handling in the analyze endpoint" without having
  opened `backend/app/routes/deals.py` in this session.
- **When summarizing or reporting on multiple files** (e.g. a task report, a PR
  description), every claim about a file's content must trace to an actual read of that
  file in the current session, not to a summary you produced earlier that may now be
  stale.
- **After any edit, re-view the file before making a second edit to it** — a prior
  `str_replace` result can look successful but the file state before your next edit
  should still be confirmed, not assumed from the diff you think you made.

---

## 6. PROCESS state files — the loop-engineering system

This repo runs as a **closed loop**, not open-ended sessions: every unit of work is a
small, scoped task that goes **Plan → Scope-lock → Implement → Verify → Self-review →
Report → Checkpoint.** Given the 5-day clock, loops here should be **small — a single
endpoint, a single node, a single converted component** — not a whole phase at once.

Read these, in order, at the start of every session, before spec docs, before code:

```
PROCESS/state.md               ← read FIRST. What's active right now? (1 task)
PROCESS/logs/<task-id>.log.md  ← read SECOND, active task only. What's been tried?
PROCESS/decisions.md           ← read before asking the user anything already answered
PROCESS/backlog.md             ← read when a task closes, to pull the next one
PROCESS/tasks/<task-id>.md     ← the task card: scope, DoD, file allowlist
```

### `PROCESS/state.md` — snapshot, overwritten every loop
```markdown
## Current
Phase: 2 (Core AI Loop)
Active task: phase2-003-risk-flagger-node
Status: in_progress (gate/fan-out edge wired, contradiction check not started)
Last checkpoint commit: 7c1a9e2
Blocked on: nothing

## Next up
phase2-004-ic-memo-drafter   ← pulled from backlog.md "Ready", not guessed

## Open questions for user
- (link to decisions.md if unresolved)
```

### `PROCESS/logs/<task-id>.log.md` — append-only scratchpad, one per task
Append a timestamped entry every time you start a sub-step, get a pass/fail result, form
a hypothesis, change approach, or hit a blocker. Raw and terse is fine.
```markdown
## 2026-07-12 14:31
POST /deals/{id}/analyze returns 500 on re-upload with a conflicting document.
Hypothesis: contradiction check assumes a prior version always exists.
Checking risk_flagger.py... confirmed: no null-check on `last_stored_summary`.

## 2026-07-12 14:50
Root cause: get_last_summary() returns None on first analysis of a deal, code
assumes a dict. Fix: guard clause, skip contradiction check on first analysis.
```
On task close, move the log to `PROCESS/logs/archive/`.

### `PROCESS/decisions.md` — append-only, permanent, ADR-style
Every product/architecture decision the user makes gets logged the same loop it's made.
**Grep this file before asking the user a question** — if it's answered, don't re-ask.
```markdown
## D-007 — pricing_advisor scope (2026-07-12)
Q: does pricing_advisor block the /analyze response if it fails?
Decision: no — it's fire-and-forget per the system design doc; on failure, omit
pricing_note from the response rather than failing the whole analyze call.
Status: LOCKED — don't revisit without explicit user instruction.
```

### `PROCESS/backlog.md` — append + prune
Anything not currently being worked on. Two rules:
1. **Anything found off-scope during a task gets logged here immediately**, not fixed
   inline and not forgotten.
2. **`state.md`'s "Next up" is always pulled from here**, never guessed. If nothing is
   `Ready`, stop and ask rather than inventing a task — this matters more than usual on
   a fixed 5-day clock, where inventing unscheduled work directly threatens the demo.
```markdown
## Ready
- [ ] phase3-002-contract-clause-extractor — depends on phase3-001, unblocked

## Blocked
- [ ] deepgram-stt-wiring — no voice sample decided for demo yet, ask user

## Deferred (found mid-task, not in that task's scope)
- [ ] doc_summarizer has no truncation for >50-page PDFs (found 2026-07-12,
      phase2-002) — not blocking the demo doc set, revisit if time allows
```

### `PROCESS/tasks/<task-id>.md` and `PROCESS/reports/<task-id>.md`
```markdown
Scope: agents/nodes/risk_flagger.py, agents/graph.py (gate/fan-out edge only)
Depends on: phase2-002 (doc_summarizer done)
Files allowed to touch: agents/nodes/risk_flagger.py, agents/graph.py
DoD:
  - [ ] risk_flags[] has severity/description/source_excerpt per item
  - [ ] gate fans out to ic_memo_drafter AND pricing_advisor via Send()
  - [ ] contradiction check flags a re-upload with changed key figures
  - [ ] pytest tests/agents/test_risk_flagger.py passes
  - [ ] curl POST /deals/{id}/analyze returns 200 with populated risk_flags
```
The matching report (written on close) is what a human reads instead of the raw log:
```markdown
## Result: ✅ DoD met
Gate: typecheck ✅ · lint ✅ · pytest 14/14 ✅ · manual curl test ✅
Deviations from spec: none
Risks: contradiction check only compares top-level figures, not nested line items
```

---

## 7. How to approach a task — the loop

0. **Verify actual state first** (Section 4 checks). Resolve or flag anything
   unexpected before step 1.
1. **Read PROCESS files in order** (Section 6), then the relevant section of
   `docs/5day-build-timeline.md` for the active phase. Know the task's DoD before
   writing code.
2. **Scope-lock before writing code.** State the file allowlist explicitly (from the
   task card). If you need a file outside it mid-task, **stop** — split the task or log
   the rest to `backlog.md`.
3. **If this is a bug fix**, follow the Debugging Protocol (Section 9) before touching
   any code.
4. **Follow the one write path.** DB writes: route handler → service function →
   `supabase-py` client, never ad-hoc SQL in a route. Storage uploads always create a
   matching `Document` row — never write to Storage without the DB record, or vice versa.
5. **Schema changes are new migrations**, never edits to old ones
   (`supabase migration new <name>`). Re-run `supabase db reset` + reseed after.
6. **Don't touch working code from an earlier phase/task** except for a confirmed bug
   (step 3), changing the minimum needed.
7. **After editing, run the gate** (Section 2) and **actually exercise the feature** —
   hit the endpoint with `curl`, run the node standalone against a real document, load
   the screen in the browser. A passing typecheck is not evidence the feature works.
8. **Self-review the diff:** is every changed file in the scope-lock list? Is anything
   "already working" touched for a reason other than a proven bug? Revert if so.
9. **Verify the DoD** on the task card is actually met — don't infer it from the gate
   passing.
10. **Close the loop:** write the report, update `state.md` (pulling "Next up" from
    `backlog.md`), log new decisions, log new off-scope findings, archive the task log.

---

## 8. Definition of "done" — no error, actually verified

"Done" requires all of:
- Gate passes (Section 2): typecheck, lint, unit tests.
- **The feature was actually run, not just compiled.** For a backend endpoint: a real
  `curl`/HTTP call with a real payload, response inspected. For a LangGraph node: run
  standalone against a real (not mocked) input document at least once. For a UI
  component: rendered in the browser with real data from the running backend, not just
  Storybook-style with hardcoded props, once its Phase reaches "wire to real data."
- **No error surfaced during that run** — not in the terminal, not in the browser
  console, not in the FastAPI logs. A feature that "mostly works but throws a warning"
  is not done; either the warning is understood and benign (say why, in the report) or
  it's a bug to fix.
- The DoD checklist on the task card is checked off item by item, not assumed from the
  gate.

If a feature *can't* be fully verified yet (e.g. its upstream dependency isn't built),
that's not "done with a caveat" — it's **blocked**, and belongs in `state.md`/`backlog.md`
as blocked, not reported as complete.

---

## 9. Debugging protocol (gate failure, wrong output, reported symptom)

1. **Reproduce first — never patch from a guess.** Write or point to a failing test or
   a reproducible `curl`/manual step. If it can't be reproduced deterministically, that
   itself is a finding — log it, don't fix blind.
2. **Isolate the layer before isolating the line.** A bug here can live in: LangGraph
   node logic (`agents/nodes/*`) → graph wiring/edges (`agents/graph.py`) → FastAPI route
   (`backend/app/routes/*`) → Supabase (schema/RLS/data) → frontend (display only —
   should never compute). A UI showing a wrong value is very often a wiring or fetch bug,
   not a node bug — check the boundary first.
3. **Distinguish a code bug from a spec/decision gap.** If the failing case reveals the
   system-design doc or `decisions.md` is itself ambiguous or silent on this case — do
   **not** silently pick an interpretation and code it. Log to `backlog.md` as blocked,
   flag it in the report, and ask the user. Code a fix only once behavior is confirmed.
4. **Log every hypothesis to the task's log, including ruled-out ones** —
   `Symptom: /analyze 500s on second upload. Hypothesis: contradiction check crashes
   on missing prior version. Ruled out: not this, get_last_summary already null-checked.
   Next: checking Send() fan-out for a race.`
5. **Time-box it.** After roughly 3 hypotheses without a confirmed root cause, stop.
   Mark the task `blocked` in `state.md`, log what's ruled out, and surface it to the
   user rather than continuing trial-and-error. On a 5-day clock this matters more than
   usual — see Section 11's cut order for what to do next.
6. **Fix only the smallest proven cause, then run the FULL gate** (not just the failing
   test) — a narrow fix can silently break another case the same way an "improved"
   `doc_summarizer` could break downstream nodes (Section 3).
7. **After a fix lands, add a regression test named for the bug**, not a generic case,
   so the reason it exists is legible to the next session.

---

## 10. Agent / sub-agent failure, timeout & runaway handling

LangGraph nodes are external-model calls in a pipeline — they fail, time out, and
occasionally loop in ways ordinary code doesn't. This is handled explicitly, never left
to fail silently:

- **Bounded retry:** every node gets **max 2 attempts** on failure (timeout, malformed
  structured output, provider error), then the node fails **loud**, not silent —
  propagate a typed error (`NodeFailure{node, attempt, reason, raw_error}`) up to the
  `/analyze` response rather than swallowing it into an empty/default value.
- **Hard step cap per graph run** (LangGraph run-level, not per-node) — prevents a
  routing bug or bad conditional edge from looping the graph indefinitely and burning
  API spend. If the cap is hit, the run stops and reports which node it was in when
  capped, not just "failed."
- **Every node run is logged** (node name, input ref, timestamp, success/fail, retry
  count, duration) — this is what the Phase 4 Agent Hub activity log reads from
  (`docs/5day-build-timeline.md` §Phase 4), and it's also your primary debugging tool
  when a run fails and the session ends before you finish investigating.
- **On any node failure or graph-run failure, tell the user explicitly** — which node,
  which attempt, the actual error (not a paraphrase), and whether it was retried. Don't
  report `/analyze` as "done" if a secondary node (e.g. `pricing_advisor`) failed
  silently in the background; report it as done-with-a-noted-gap, per Section 8.
- **Distinguish a stuck run from a slow run before declaring failure** — if a node is
  taking unusually long, check the activity log / Checkpointer state for actual progress
  before assuming it's hung and killing it; report what you observed either way.
- **`pricing_advisor` (node 3.4) is explicitly secondary** — per the timeline's Section
  7 cut order, its failure must **never** block or degrade the response from
  `doc_summarizer` → `risk_flagger` → `ic_memo_drafter`. Wire it so its failure only
  omits `pricing_note` from the response, nothing else.
- **Citations from `web_search`/`web_fetch` must be parsed from the response's
  structured `citations` array, not fabricated or inferred** — if a node's output makes
  a claim that should be sourced but the citations array is empty, that's a node-level
  finding to report, not something to patch by inventing a plausible-looking source.

---

## 11. Non-negotiable invariants

- **The demo-critical path is never cut, under any time pressure:** Analyst Lead
  pipeline (3.1→3.2→3.3), the Dashboard, and the `deal_id` scope filter on
  notebook-scoped chat. A chat that blends data across deals undermines the platform's
  core trust story — this is the one UI behavior treated as seriously as a money/auth
  bug in a normal build.
- **Model calls only through the `call_model()` adapter** (Section 1) — never a direct
  SDK call in a node.
- **Every document upload creates a Storage object AND a `Document` row together** —
  never one without the other.
- **Schema changes are new migrations, never edits to applied ones.**
- **Secrets never committed; startup fails fast on a missing required key**, named
  explicitly, never a silent downstream failure.
- **`/chat` WebSocket and `/deals/{id}/analyze` must degrade to a visible error state in
  the UI on failure** — never a spinner that hangs forever with no feedback; this is a
  live-demo risk, not just a UX nicety.
- If the Section 7 cut order (below) needs to be invoked, **log the cut to
  `decisions.md` and tell the user** — don't quietly drop scope without a record of it.

---

## 12. Time-pressure cut order (from `docs/5day-build-timeline.md` §7)

If a phase is running over and something must be cut to protect the demo, cut **in this
order** — never out of order, and never something not on this list without asking:

1. `pricing_advisor` node (Phase 2) — already secondary; stub or skip.
2. Contradiction check on re-upload (Phase 2) — dropping it means re-analysis silently
   overwrites instead of flagging; acceptable for a first demo.
3. Contracts Lead clause-extraction detail (Phase 3) — keep summarization, drop
   fine-grained clause labeling.
4. Chat streaming (Phase 3) — fall back to plain request/response if WebSocket work
   runs long.
5. Deal Detail's full tab set (Phase 4) — ship Overview + Analysis only; present
   Industries/Company/Tasks tabs as design-doc screens for the demo.

**Never cut**, at any point: the Analyst Lead pipeline, the Dashboard, and the
`deal_id` filter on notebook-scoped chat (Section 11). If protecting these requires
cutting everything above, do that.

---

## 13. Where things live

```
frontend/src/pages/                Dashboard, Deal Detail, Chat, Agent Hub (static log)
frontend/src/components/           design-tokens-first: Stage Diagram, Deal card,
                                    Kanban, Table view, Chat panel, Agent activity pill
backend/app/routes/                deals.py, contracts.py, chat.py (WebSocket)
backend/app/services/              one write path per resource — no bare supabase
                                    calls from routes
agents/graph.py                    Orchestrator router + gate/fan-out edge structure
agents/nodes/                      doc_summarizer, risk_flagger, ic_memo_drafter,
                                    pricing_advisor (3.1→3.4)
agents/adapters/model_adapter.py   call_model() — the only path to any LLM provider
supabase/migrations/               NNNN_<domain>_<change>.sql, append-only
supabase/seed/                     2–3 example deals incl. "Deal A" worked example
docs/system-architecture.md        full 21-agent design (source of truth for intent)
docs/ux-ui-spec.md                 UX/UI design spec, design tokens, 11 screens
docs/5day-build-timeline.md        THIS WEEK's build order, scope table, cut order
PROCESS/state.md                   current task snapshot — read first, every session
PROCESS/decisions.md               locked decisions (ADR-style) — grep before asking
PROCESS/backlog.md                 ready/blocked/deferred work
PROCESS/tasks/<task-id>.md         task cards: scope, file allowlist, DoD
PROCESS/logs/<task-id>.log.md      per-task append-only scratchpad
PROCESS/reports/<task-id>.md       per-task human-readable result report
```

---

## 14. Commit & PR discipline

- Small, phase-scoped commits; imperative subject (`add risk_flagger contradiction check`).
- A commit/checkpoint must pass the full gate (Section 2) and include a real,
  manually-verified run of the feature it adds (Section 8).
- If a change spans phases (e.g. wiring a Phase 1 UI component to a Phase 2 endpoint),
  say so in the commit/PR description.
- Reference the closed task-id and its report (`PROCESS/reports/<task-id>.md`) so a
  reviewer — including a future session of yourself — gets the summary without reading
  the raw log or diff.

---

## 15. When unsure

- **Check `PROCESS/decisions.md` first.** If already decided, apply it — don't re-ask.
  If genuinely new, ask, then log it there in the same loop (Section 6).
- Prefer a short clarifying question over guessing on: **the cut order, and anything
  touching the `deal_id` scope filter** — those are the places a wrong guess costs the
  most this week.
- If a requested change would break an invariant in Section 11, stop and flag it rather
  than implementing it.
- If a requested change is out of scope for the active task, log it to
  `PROCESS/backlog.md` — don't silently expand scope on a 5-day clock.
- Tunable values (which model per agent, retry counts, step caps, allowed_domains for
  web_search) belong in config, not hardcoded inline.
