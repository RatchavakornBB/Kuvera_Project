# Kuvera Capital — Demo Script

Written per 5day-build-timeline.md's Phase 5 block (13:30–14:30). This is a rehearsed script, not
an improvised walkthrough — every claim below was verified against the real running app, not the
design docs, as of 2026-07-13 (see PROCESS/reports/ for the underlying verification of each screen).

## 1. One-sentence framing

"Kuvera Capital is an AI Deal-Ops platform for M&A — instead of an analyst manually reading a
100-page contract, the system reads it, flags the risks, drafts the IC memo, and lets you just ask
it questions about the deal in plain language."

## 2. Before you start

- Start Supabase (`supabase start`), backend (`uvicorn app.main:app --app-dir backend --port 8000`
  from repo root using `backend/.venv`), frontend (`npm run dev` in `frontend/`, port 5173).
- Confirm `GET http://localhost:8000/health` returns 200 before opening the browser.
- Open `http://localhost:5173/` in a fresh tab — Dashboard, Board view, should show 3 real deals.
- Have this script open on a second monitor/window, not the screen being shared.
- **Do not** click "Regenerate" on the Analysis tab live unless you have 5+ spare minutes — a real
  end-to-end Analyst Lead run (4 sequential/parallel real Claude API calls) takes ~2–3 minutes.
  Show the already-computed real results instead; mention regeneration is one click away.

## 3. Click path (~10–12 minutes core path)

| # | Screen / action | What to say | Why it matters |
|---|---|---|---|
| 1 | Dashboard, Board view | "Three real deals, pulled live from Postgres — not mocked. Each card shows the real stage, a risk-flag count, and an owner." | Establishes everything downstream is real, not a static mock |
| 2 | Click **Table**, then **Pipeline** view toggle | "Same data, three lenses — a partner wants a funnel view, an analyst wants a worklist." | Shows UI depth without new data |
| 3 | Point at **Needs attention** rail (Horizon Freight Corp) | "This isn't manually curated — it's deals stalled past a threshold, computed automatically." | Shows an automated ops signal, not busywork |
| 4 | Point at the bell icon (badge showing 1) | "A real key-date check — this contract has a non-renewal deadline in 19 days, computed fresh, not hardcoded." | Segues into Deal Detail naturally |
| 5 | Click into **Deal A** | "Real header, real Stage Diagram driven by `stage_entered_at`." | — |
| 6 | **Overview** tab | Point at timeline, contacts, key dates — "all from the same `/deals/{id}` payload." | Shows the data model is coherent, one fetch |
| 7 | **Documents** tab | "Required-documents checklist — one received, one still pending. Below it, the real file library." Optionally: click **+ Add file** and upload a real PDF live — this *is* fast (~1s) since it's just Storage + a DB row, no LLM call yet. | Proves the upload path is real, and is fast enough to do live |
| 8 | **Analysis** tab | "This is the Analyst Lead — a LangGraph subgraph. It read the actual MSA contract and produced this." Walk through: risk flags grouped high/medium (point at the change-of-control flag — the most M&A-relevant one), the IC memo draft, the collapsed pricing section. | The centerpiece — show real AI output, read one risk flag aloud |
| 9 | **Tasks & Notes** tab | "Real task list — add one live." Type a task, hit Add, watch it appear immediately (no refresh). Check it done. | Cheap, fast, tangible proof of a real write path |
| 10 | Click **Ask Kuvera Assistant** (top-right, from within the deal) | "This opens the Orchestrator, already scoped to Deal A — it can't see other deals' data even if asked, that's structural, not a prompt instruction." Ask something like *"What's the biggest risk in this deal?"* | The Orchestrator + Concierge Q&A, deal-scoped by design (agents/deal_context.py) |
| 11 | Sidebar → **Documents & Contracts** | "Same documents, but cross-deal — search, filter by deal/type/status." Type a search term, show it narrow the list. Click a row to open the real extracted-clauses side panel. | Shows the Contracts Lead's output (4.1/4.2) independent of the per-deal view |
| 12 | Sidebar → **Agent Hub** | "This is a real trace of what the Analyst Lead actually did — reconstructed from LangGraph's own Postgres checkpoint state, not a separate log I wrote by hand. Every row here is a real historical run." | Operational transparency — proves the multi-agent claim isn't just marketing |
| 13 | Back to Dashboard | "And that's the full loop — pipeline, deal, documents, AI analysis, chat, all one system." | Close the loop |

### Optional bonus step (~2 min, if time and interest allow)

| # | Screen / action | What to say | Why it matters |
|---|---|---|---|
| 14 | Sidebar → **Admin** → **Skills** tab | "This is real governance, not a mockup — pick an agent, edit its instructions." Select an agent, type a one-line addition, show the real diff view. | Sets up the payoff in step 15 |
| 15 | **Propose change** → **Pending Approvals** tab → **Approve** | "Nothing takes effect until it's approved — same pattern a PR review would use." Approve it. | Shows the review gate is real, not decorative |
| 16 | **Audit Log** tab | "And it's logged — who changed what, when." Point at the real timestamped entry. | Closes the governance loop visibly |

Note: the change only takes effect on the *next* real Analyst Lead run for that agent — don't
re-trigger a live analysis just to prove it (see the "do not click Regenerate live" note above).
If asked "does this actually work," the honest answer is yes, and it was verified with a raw
`call_model()` test during development, not just this UI.

## 4. Live vs. design-only — have this ready if asked directly

| Feature | Status |
|---|---|
| Dashboard (Board/Table/Pipeline), Deal Detail (all 4 tabs), Documents & Contracts, Chat/Orchestrator | **Live** — real Postgres, real Storage, real Claude API calls, no mocked data anywhere |
| Analyst Lead (3.1–3.4: doc summarizer, risk flagger, IC memo, pricing) | **Live** — real LangGraph graph, Postgres Checkpointer, verified end to end including a real contradiction-check hit during testing |
| Contracts Lead (4.1 summarizer, 4.2 clause extractor) | **Live** |
| Concierge Q&A + Orchestrator routing (web search, SEC EDGAR) | **Live** — real `web_search` tool, real SEC EDGAR API calls |
| Key-date notifier | **Live**, but on-demand/polled, not a true server cron (no task-queue infra in a 5-day build) |
| Agent Hub | **Live**, but a static activity log reconstructed from checkpoints — not the full 21-agent grid / live graph view from the design doc |
| Semantic document search | **Not live** — substring search on name/summary; real pgvector semantic search needs an embeddings pipeline not built in this MVP |
| Admin & Skill Governance (Agents & Models, Skills, Pending Approvals, Audit Log) | **Live** — real DB-backed config wired into the actual `call_model()` call; an approved skill/model change genuinely changes the next real Claude API call. Verified by approving a real skill change and confirming the next Claude response reflected it. Knowledge Base tab and eval pass-rate bar are not built — nothing real backs either (no Knowledge Agent, no eval framework) |
| Drafting Lead (5.1 doc/email prep, 5.2 deck prep) | **Design-only** — not built |
| Knowledge Agent / Learning Agent (background promotion + outside-world ingestion) | **Design-only** — not built |
| Full contradiction/hypothesis confidence-scoring engine | **Design-only** — the *lightweight* version (a visible flag, no scoring) is live |
| RBAC / multi-user auth | **Not built** — single demo user, no login screen, no role gating |
| Cloud deploy | **Not done** — local + screen-share for this demo (see PROCESS/backlog.md) |

## 5. Rehearsed one-liners for "what about X?"

- **"Is any of this data fake / hardcoded?"** — "No — every screen you just saw is backed by a real
  Postgres query and, for the AI outputs, a real Claude API call. I can show you the network tab if
  you want proof live."
- **"What about role-based access / multiple users?"** — "Not built in this MVP — there's one demo
  user and no login screen. The schema has an `owner_id` on every deal, so RBAC is a real next step,
  not a redesign."
- **"What about the Skill governance / model-swap admin screen?"** — "That's actually live now — the
  Admin screen. I can propose a skill change for an agent, approve it, and the very next real Claude
  call for that agent uses it — I verified that end to end. The Knowledge Base tab and eval
  pass-rate scoring from the design doc aren't built, since there's no Knowledge Agent or eval
  framework yet to honestly back them."
- **"Does the Agent Hub show all 21 agents live?"** — "Right now it's a real activity log of the
  Analyst Lead's 4 nodes, reconstructed from LangGraph's own checkpoint state — genuinely real, not
  a mock, but scoped down from the full live-graph view in the design doc on purpose, per the
  5-day timeline."
- **"What about the Learning Agent / Knowledge Agent?"** — "Not built — those are background
  services in the architecture for promoting patterns across deals and ingesting outside news. Out
  of scope for a 5-day MVP; the deal-scoped Concierge Q&A and web-search tool are the live
  equivalent for this build."
- **"Is the semantic search real (pgvector)?"** — "Not yet — it's substring search on the document
  name and AI summary right now. Wiring up embeddings is a schema + pipeline change, logged as a
  known gap, not something I tried to fake."
- **"What happens if I upload a bad/huge file?"** — honest answer if asked live: "Upload isn't
  validated by file type/size yet — that's a real gap I'd fix before production, not before a demo."
- **"Is this deployed anywhere?"** — "Running locally against a local Supabase instance for this
  demo. A cloud deploy is a documented optional step — happy to do it if a shareable link is more
  useful than a screen-share."

## 6. Fallback plan

- If the backend or Supabase isn't responding: restart in this order — `supabase start` (wait for
  all services healthy) → backend → frontend. `GET /health` should return 200 before touching the UI.
- If a live click (e.g. the Documents-tab upload) fails on stage: don't debug live — say "let me
  show you the version I ran earlier" and narrate from a saved screenshot/this script's talk track
  instead of troubleshooting in front of the interviewer.
- If asked to go off-script into a screen not covered above, it's fine to say "that one's not built
  yet — here's what the design doc says" and pull up the relevant section of `docs/system-architecture.md`
  or `docs/ux-ui-spec.md` directly, rather than pretending it's live.
