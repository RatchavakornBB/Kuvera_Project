# KUVERA CAPITAL — 5-Day MVP Build Timeline

Execution plan from design (System Architecture + UX/UI docs) to a working, demo-ready prototype.
v1.0 | Confidential | Interview Submission

---

## 1. Scope & Philosophy

This timeline turns the System Architecture and UX/UI design docs into a working prototype across five phases
over 4–5 working days. The full 21-agent architecture is not buildable end to end in that window — this plan
draws a hard, explicit line between what runs live for the demo and what is presented through the design docs,
so effort goes toward a working core loop rather than a partially-built everything.

| Runs live (built this week) | Design-only (presented via the two docs, not built) |
|---|---|
| Deal Management DB (8 models) + Dashboard + Deal Detail core tabs | Learning Agent continuous ingestion |
| Receiver → Orchestrator → Analyst Lead pipeline (3.1→3.2→3.3, real Claude API calls) | Skill self-creation governance UI |
| Contracts Lead (summarize, clause extract) | RBAC / multi-team deal walls (Phase 3) |
| Concierge Q&A (lightweight RAG over seeded data) + deal_id-scoped "notebook" chat filter | Company Library RAG tuning controls |
| Lightweight contradiction flag on re-upload (new value vs. last stored value, no scoring) | Full Contradiction & Hypothesis confidence-scoring engine (Section 10.5) — status ranks, corroboration counting, versioned promotion into Knowledge Agent |
| Chat interface (Orchestrator persona) | NotebookLM export bridge |
| Web search / SEC EDGAR fetcher (Analyst tool) | Full real-time Agent Hub graph view (a static/log version ships instead) |

### 1.1 Environment Decision (confirmed)

- Supabase runs locally via Docker (Supabase CLI) — full Postgres/Auth/Storage/pgvector parity with the
  cloud product, zero setup friction, no dependency on internet access during development or demo.
- Frontend and backend run as local dev servers (or their own Docker containers) alongside the Supabase
  stack — a cloud deploy is a Phase 5 optional step, not a dependency for the demo itself.

---

## 2. Environment & Tooling Setup

Done once, before Phase 1 work starts — targeting under 90 minutes.

| Step | Detail |
|---|---|
| Repo structure | `/frontend` (React + Vite), `/backend` (FastAPI), `/supabase` (CLI-managed migrations + seed), `/agents` (LangGraph graph + node definitions) |
| Supabase local | `supabase init && supabase start` — provisions Postgres, Auth, Storage, Realtime, pgvector locally via Docker |
| Secrets | `.env` (gitignored): `ANTHROPIC_API_KEY`, (optional) `OPENAI_API_KEY` / `GOOGLE_API_KEY` for the multi-provider model_id design, `DEEPGRAM_API_KEY`, `SUPABASE_URL`/`KEY` (local values from `supabase start` output) |
| Python env | FastAPI, langgraph, langchain-anthropic, supabase-py, python-dotenv |
| Node env | React 18, Vite, TanStack Query, Tailwind (matches the UX doc's design tokens directly) |

---

## 3. Converting the Claude Design Mockup to Real Frontend

The Claude Design output (`.dc.html`: `Kuvera_Capital_dc.html` — 2,824 lines, `StageDiagram_dc.html`) is a
preview/spec format — custom `x-dc`/`sc-for`/`sc-if` directives plus a `DCLogic` class — built for rendering inside
Claude Design's own preview engine, not for deployment. It is not React and cannot be served as-is; it is
high-value as a visual and interaction reference, converted deliberately rather than run directly.

### 3.1 Conversion Mapping

| Claude Design pattern | Converts to (React) | Notes |
|---|---|---|
| `<x-dc>` root + component class extending `DCLogic` | A functional React component; `DCLogic.renderVals()` logic becomes derived state (`useMemo`) or plain render-time calculation | The `DCLogic` class's return shape from `renderVals()` maps almost 1:1 to a component's derived-props object |
| `sc-for list="{{ items }}" as="item"` | `.map((item) => (...))` over the same array | `hint-placeholder-count` attributes (used for Claude Design's preview skeletons) are dropped — no runtime equivalent needed |
| `sc-if value="{{ cond }}"` | `{cond && (...)}` or a ternary in JSX | Where `sc-if` drives a boolean like `showLabels`, this becomes a straightforward prop-driven conditional |
| `data-props` JSON schema (editor/default/tsType per prop) | TypeScript prop interface on the React component | The `tsType` field in the schema is literally the type annotation to use — this step is close to mechanical, not creative |
| Inline style strings with hex values (e.g. `background:{{ seg.bg }}`) | Tailwind utility classes or CSS custom properties matching the palette in the UX doc (Section 1.2) | Hex values carry over unchanged (e.g. `#6D5EF5` Signal Violet); only the authoring syntax changes |

### 3.2 Worked Example — Stage Diagram

`StageDiagram_dc.html` is small enough to show the full conversion end to end — the same pattern scales to
every other component in the larger file.

| Claude Design source | React equivalent |
|---|---|
| `STAGE_SHORT` array + `Component.renderVals()` computing bg/border/labelColor per segment from status | A plain TS function `mapStageSegments(segments)` returning the same shape, called at render time or memoized with `useMemo` |
| `<sc-for list="{{ segs }}" as="seg">...<div style="...background:{{ seg.bg }}">` | `segs.map((seg) => <div key={seg.name} className={segClass(seg.status)} title={seg.title} />)` |
| `<sc-if value="{{ showLabels }}">` | `{variant === 'full' && <span className="stage-label">{seg.short}</span>}` |
| `variant` prop (`"compact"` \| `"full"`) driving `barHeight`/`showLabels` | Same prop, same two variants — becomes a TS union type `'compact' \| 'full'` |

### 3.3 Component Inventory & Effort Estimate

Breaking the larger `Kuvera_Capital_dc.html` file (148 `sc-for` loops, 172 `sc-if` conditionals) into discrete
components with a rough conversion estimate each — used to build the Phase 1–4 schedule in Section 6:

| Component | Est. time | Depends on |
|---|---|---|
| Design tokens file (colors, spacing, type scale) | 45 min | None — build first, everything else imports from it |
| Stage Diagram (compact + full variant) | 45 min | Design tokens |
| Deal card (Board view) | 45 min | Stage Diagram, design tokens |
| Kanban column + Board view layout | 1 hr | Deal card |
| Table view (dense rows) | 1 hr | Stage Diagram, design tokens |
| Pipeline funnel strip | 45 min | Design tokens |
| Filter bar + header row | 30 min | Design tokens |
| Deal Detail header + tab shell | 1 hr | Stage Diagram |
| Overview tab (timeline, POC card, key dates) | 1.5 hr | Deal Detail shell |
| Documents tab (checklist + AI summary preview) | 1 hr | Deal Detail shell |
| Analysis tab (risk cards, IC memo panel, pricing collapsed) | 1.5 hr | Deal Detail shell |
| Chat panel (message thread, composer, inline artifact card) | 2 hr | Design tokens |
| Agent activity pill component | 30 min | Design tokens — reused in chat and Agent Hub |

Total: roughly 12–13 hours of conversion work, which is why Section 6 spreads it across Days 1, 3, and 4 rather
than attempting it in one block.

---

## 4. Backend Management

### 4.1 API Layer (FastAPI) — Endpoint Detail

| Endpoint | Method | Request / Response |
|---|---|---|
| `/deals` | GET | Query params: `stage`, `industry`, `owner`. Response: array of `Deal` with nested current-stage + status rollup, matching the Dashboard's Table view fields |
| `/deals` | POST | Body: `name`, `client`, `industry`, `assigned team member`. Creates a Deal at stage "Lead" |
| `/deals/{id}` | GET | Full Deal record + nested `Contact`/`Document`/`Task`/`MeetingNote`/`DDItem`/`Milestone` — the payload Deal Detail's tabs render from directly |
| `/deals/{id}/documents` | POST (multipart) | Uploads a file to Supabase Storage, creates a Document row with status 'received', and enqueues Receiver-tier normalization |
| `/deals/{id}/analyze` | POST | Body: `document_id`. Triggers the Analyst Lead subgraph synchronously for the demo (no background queue needed at this scale); Response: `summary`, `risk_flags[]`, `ic_memo_draft` |
| `/deals/{id}/tasks` | POST / PATCH | Create/update a Task row — backs the Tasks & Notes tab |
| `/contracts` | POST (multipart) | Uploads a contract, triggers 4.1 Contract Summarizer + 4.2 Clause Extractor; Response: `summary`, `clauses[]` |
| `/chat` | WebSocket | Bidirectional stream — client sends `{message, deal_id?}`, server streams Orchestrator tokens plus any inline artifact events, matching the UX doc's streaming chat pattern |

### 4.2 LangGraph Runtime — Node by Node (Analyst Lead)

The subgraph actually built this week, matching Figure 4 in the system design doc exactly — no shortcuts taken
on the gate/fan-out structure itself, only on surrounding scaffolding (evals, model swapping) that the MVP
doesn't need to prove:

| Node | Input | Output | Model call |
|---|---|---|---|
| 3.1 `doc_summarizer` | Uploaded document text (post-Receiver normalization) | `summary: string` | Single Claude call, document content block |
| 3.2 `risk_flagger` | summary + original document | `risk_flags: [{severity, description, source_excerpt}]` | Single Claude call, structured output |
| gate (edge, not a node) | Waits for 3.2 to complete | Fans out to 3.3 and 3.4 via LangGraph's `Send()` | No model call — pure graph logic |
| 3.3 `ic_memo_drafter` | summary + risk_flags | `ic_memo_draft: string` (markdown) | Single Claude call |
| 3.4 `pricing_advisor` | summary + risk_flags | `pricing_note: string` (marked secondary in the UI per the system design doc) | Single Claude call — can be stubbed/skipped first if Phase 2 runs long, per Section 7 |

- Orchestrator implemented as a minimal conditional-edge router this week: enough intent classification
  to send a chat message to either the Analyst subgraph or a simple RAG-over-seed-data answer path —
  the full hybrid hard-route/LLM-route split from Section 5 of the system design doc is design-only for this
  build.
- Supabase Postgres as the Checkpointer backend from day one — the same mechanism specified for
  production, not a shortcut, so nothing needs rearchitecting later.
- Error handling kept lightweight but present: a bounded retry (2 attempts) on node failure and a hard
  step cap per run, covering the core of Section 14 without building the full circuit-breaker/Agent-Hub
  degraded-state UI this week.

### 4.3 Database

- Migrations written directly from the Section 3.1 schema table — 8 models, foreign keys to Deal
  throughout, run via `supabase migration new` + `supabase db reset` for repeatability.
- Seed script (SQL or a small Python script using supabase-py) loads 2–3 example deals, including the
  "Deal A" worked example from the system design doc, so the demo has real data on first run — written
  once in Phase 1, reused (reset + reseed) throughout the week as schema changes.

### 4.4 Auth (light)

- Supabase Auth enabled with a single seeded demo user — full RBAC role differentiation (Partner/Deal
  Lead/Analyst/Admin/Viewer) is Section 15/Phase 3 territory and stays design-only this week; the demo
  runs as one authenticated user throughout.

---

## 5. Tools & API Integration Management

### 5.1 Claude API — Multi-Provider Adapter

Even though only Claude is actually called this week, the adapter is built now so nothing needs restructuring
when OpenAI/Gemini are added per the system design doc's model_id design:

- A single `call_model(agent_name, messages, tools=[])` function; internally it looks up `agent_name`'s
  `model_id` from a small config table/dict and dispatches to the right SDK client.
- Every LangGraph node calls through this one function — never the Anthropic SDK directly — so adding a
  second provider later is a config change, not a code change in every node.

### 5.2 web_search / web_fetch

- Added directly to the Analyst Lead's tool list as the official Anthropic server tools (not a custom scraper)
  — this is the exact gap identified earlier in this project's Q&A when a prior attempt got no citations back.
- Citations parsed explicitly from each response's `citations` array (`url`, `title`, `cited_text`) and stored
  alongside the summary/risk flags, then rendered as clickable source links in the Analysis tab — the API
  returns them as structured JSON, not as ready-made markdown links, so this rendering step is not
  optional.
- `allowed_domains` left unset by default for the demo (broadest access); only set it if a specific demo
  scenario calls for restricting to known-good sources.

### 5.3 SEC EDGAR Fetcher

- No API key required — only a compliant User-Agent header (app name + contact email) per SEC's fair-use policy.
- Two-step call: (1) CIK lookup by company name/ticker against SEC's `company_tickers.json`, (2) filing fetch
  against `data.sec.gov`'s submissions endpoint for that CIK, filtered to form type 10-K/10-Q/20-F.
- Hard-routed per the system design doc's Section 5 routing rules — implemented as a plain conditional in
  the Analyst Lead's tool-selection step, not a call through the Orchestrator's LLM router.

### 5.4 Deepgram (STT) & File Reading

- Deepgram used only if the demo includes a voice/meeting-note example — otherwise safe to stub (a
  fixed sample transcript) for the week rather than spending setup time on it.
- PDF reading via Claude's native document content blocks; images via base64 image content blocks —
  both native to the Claude API, no extra service required, and already covered by the multi-provider
  adapter in 5.1.

### 5.5 Secrets Management

- All keys in `.env`, never committed; a single `config.py`/`config.ts` validates required keys at startup and fails
  fast with a clear error naming the missing key, rather than failing silently mid-request during the demo.

---

## 6. Phase-by-Phase Timeline (Hour-Level)

Each day assumes roughly an 8–9 hour working block; adjust start/end times to your actual schedule, the
sequencing and durations are what matter.

### Phase 1 — Foundations

| Time | Task | Output / checkpoint |
|---|---|---|
| 09:00–10:00 | Environment setup (Section 2): repo structure, `supabase init && supabase start`, `.env` with all keys, Python + Node dependency install | `supabase status` shows all services running locally |
| 10:00–11:30 | Write migrations for all 8 models (Section 4.3) + run `supabase db reset` | Schema visible in Supabase Studio (local), all foreign keys to Deal correct |
| 11:30–12:30 | Write and run seed script — 2–3 deals including "Deal A" | Querying `/deals` (even via curl, before frontend exists) returns real seeded rows |
| 13:30–14:15 | Design tokens file (Section 3.3, item 1) | Colors/spacing/type scale importable into any component |
| 14:15–15:00 | Convert Stage Diagram (Section 3.2) | Renders correctly for a deal at each of the 7 stages |
| 15:00–16:00 | Convert Deal card + Kanban column shell | A single hardcoded deal card renders with correct styling |
| 16:00–17:30 | Wire Dashboard to real `/deals` data (Board view), Table view | Dashboard loads seeded deals from the real API, Stage Diagrams correct per deal |
| 17:30–18:00 | Buffer / commit checkpoint | End of Phase 1: Dashboard is a real, data-backed screen |

### Phase 2 — The Core AI Loop

| Time | Task | Output / checkpoint |
|---|---|---|
| 09:00–10:00 | FastAPI scaffold: app structure, `/deals` GET/POST/GET-by-id wired to Supabase | Endpoints return real data, testable via curl/Postman |
| 10:00–11:00 | `/deals/{id}/documents` upload endpoint → Supabase Storage + Document row | Uploading a PDF creates a real storage object and DB row |
| 11:00–12:30 | LangGraph: model adapter (Section 5.1) + 3.1 `doc_summarizer` node, tested standalone against a real uploaded PDF | Calling the node directly returns a real Claude-generated summary |
| 13:30–15:00 | 3.2 `risk_flagger` node + the gate/fan-out edge structure + a lightweight contradiction check (Section 10.5, scoped-down): on re-analysis, diff the new summary's key figures against the last stored version and flag mismatches — no confidence scoring or hypothesis status this week, just a visible flag for the user to resolve | Risk flags generated from the summary, structurally correct (severity, source excerpt); re-uploading a conflicting document surfaces a flag instead of silently overwriting |
| 15:00–16:00 | 3.3 `ic_memo_drafter` node (3.4 `pricing_advisor` if time allows, else stub per Section 7) | A markdown IC memo draft comes out the other end of the graph |
| 16:00–17:00 | `/deals/{id}/analyze` endpoint wiring the whole subgraph together end to end | One API call: upload happened earlier, now POST `/analyze` returns `summary` + `risk_flags` + `ic_memo_draft` in one response |
| 17:00–18:00 | Manual end-to-end test with a real financial document + buffer | End of Phase 2: the core AI loop (Requirement 1 & 3) works, even if only testable via API calls, not yet in the UI |

### Phase 3 — Contracts, Concierge, Chat

| Time | Task | Output / checkpoint |
|---|---|---|
| 09:00–10:30 | Contracts Lead: `/contracts` endpoint, 4.1 summarizer + 4.2 clause extractor nodes | Uploading a sample contract returns a summary and a clause list |
| 10:30–12:00 | Concierge Q&A: RAG over seeded deal data with a `deal_id` filter applied on the "Ask about this deal" panel (Section 4.5's notebook-scoped mode) — global chat, if built, skips this filter; full `agent_scope` filtering across every field stays design-only per Section 10.4 | Asking "what's the status of Deal A" from Deal A's panel returns a correct, grounded, citation-backed answer scoped only to Deal A's sources |
| 13:00–15:00 | Convert Chat panel components (message thread, composer, inline artifact card) per Section 3.3 | Chat UI renders hardcoded sample messages correctly, styled per the UX doc |
| 15:00–16:30 | Wire Chat panel to `/chat` WebSocket — Orchestrator routes between Concierge Q&A and Analyst subgraph based on message content | Typing a question in the real UI gets a real streamed answer |
| 16:30–17:30 | web_search / web_fetch + SEC EDGAR tool wiring on the Analyst Lead (Section 5.2–5.3) | Asking about a public comparable company triggers a real web search or EDGAR fetch with visible citations |
| 17:30–18:00 | Buffer / commit checkpoint | End of Phase 3: Chat, Contracts, and web research all functional |

### Phase 4 — Integration

| Time | Task | Output / checkpoint |
|---|---|---|
| 09:00–11:00 | Convert Deal Detail shell + Overview tab (Section 3.3) | Clicking a deal from the Dashboard opens a real Deal Detail page with correct header/Stage Diagram |
| 11:00–12:30 | Convert Documents tab + wire to real upload/analyze flow from Phase 2 | Uploading a document in the real UI triggers real analysis and shows the result |
| 13:30–15:00 | Convert Analysis tab (risk cards, IC memo panel, pricing collapsed) + wire to `/analyze` response | Risk flags and IC memo draft render correctly in the real UI, matching the UX doc's layout |
| 15:00–16:00 | Light Agent Hub: a static activity log table (which node ran, when, success/fail) reading from LangGraph Checkpointer state — not the full live graph view | A simple page shows a real trace of what the Analyst subgraph actually did on the last run |
| 16:00–17:30 | Full integration pass: Dashboard → Deal Detail → Chat as one uninterrupted flow, fix any broken links/state between screens | A user can complete the entire demo path without a developer intervening |
| 17:30–18:00 | Buffer / commit checkpoint | End of Phase 4: the whole demo path works start to finish |

### Phase 5 — Polish & Rehearsal

| Time | Task | Output / checkpoint |
|---|---|---|
| 09:00–11:00 | Bug fixing pass across the full flow, prioritized by what the demo script (below) actually touches | No visible errors during a full run-through |
| 11:00–12:30 | Visual polish: spacing, empty states, loading states (Agent activity pill) matching the UX doc's Section 1.4 patterns | The app looks intentional, not just functional |
| 13:30–14:30 | Write the demo script: exact click path, which screens are live vs. presented from the design docs, and a rehearsed one-line answer for likely "what about X" questions (Learning Agent, RBAC, Skill governance, etc.) | A written script exists, not an improvised walkthrough |
| 14:30–15:30 | Rehearse the demo twice, timed | Demo fits comfortably in the interview's time slot |
| 15:30–17:00 | Optional: cloud deploy (Supabase cloud project + frontend/backend hosting) if a shareable URL is wanted, per Section 1.1 | A public URL, if pursued — skip this block entirely if local + screen-share is sufficient |
| 17:00–18:00 | Final buffer | End of Phase 5: rehearsed, working demo ready |

---

## 7. Risk & Fallback (Cut Order)

If a phase runs over, cut in this order — protecting the core "upload → AI analysis → answer" loop above all
else, since that is what most directly demonstrates Requirements 1 and 3:

1. **1st to cut:** 3.4 `pricing_advisor` node (Phase 2) — already marked secondary in the system design doc;
   skip or stub it without weakening the core loop.
2. **2nd to cut:** the lightweight contradiction check on re-upload (Phase 2) — it's already a scoped-down
   stretch item this week; dropping it just means re-analysis silently overwrites instead of flagging,
   acceptable for a first demo.
3. **3rd to cut:** Contracts Lead clause extraction detail (Phase 3) — keep summarization, drop fine-grained
   clause labeling.
4. **4th to cut:** Chat streaming (Phase 3) — fall back to a simple request/response chat if WebSocket work
   runs long.
5. **5th to cut:** Deal Detail's full tab set (Phase 4) — ship Overview + Analysis only, present
   Industries/Company/Tasks as design-doc screens for this demo.

**Never cut:** the Analyst Lead pipeline (3.1→3.2→3.3), the Dashboard, and the deal_id filter on notebook-
scoped chat (a chat that blends deal data across notebooks undermines the exact trust story the demo is
making) — these are what make the rest of the design doc credible; everything else can be explained
verbally against the UX doc if time runs out.
