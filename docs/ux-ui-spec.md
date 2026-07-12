# KUVERA CAPITAL — UX / UI Design Specification

Frontend Design for the AI Operating Platform — companion to the System Architecture document.
v1.0 | Confidential | Interview Submission

---

## 1. Design Principles & Direction

### 1.1 Philosophy

Modern, tech-forward, AI-native — with a deliberate lean toward the trading-terminal / corporate-finance register (Bloomberg, Refinitiv-style density) rather than a generic SaaS look, since the audience is M&A and advisory professionals who live in dense data screens all day. Four principles guide every screen:

- **Terminal density, not startup whitespace** — dark surface by default, hairline grid borders on tables instead of soft floating cards, tighter type scale. The interface should feel like it belongs next to a Bloomberg terminal, not a marketing dashboard.
- **Show the AI working, don't hide it** — when an agent is analyzing a document or drafting a memo, the UI shows that as a visible, named process ("Risk flagger reviewing 3 documents"), not a generic spinner. This builds trust and matches the multi-agent architecture underneath.
- **Every number is a live figure, not a snapshot** — deal stages, risk counts, and pipeline totals read like ticking terminal data (monospace, right-aligned, updated timestamp always visible), reinforcing that this is a live operating system, not a static report.
- **Every AI output is provisional until reviewed** — nothing an agent produces (a risk flag, a price suggestion, a summary) looks visually "final." Confidence/error indicators (Section 4.2) and explicit approve/reject actions are always present, tying directly to the Data-Driven Readiness Evaluation framework in the system design doc.

### 1.2 Color Palette

Dark surface is the default (trading-terminal register); a light mode variant swaps Canvas/Ink but keeps every accent color identical.

| Color | Hex | Usage |
|---|---|---|
| Terminal Black (primary surface) | `#0B0C0F` | Default page background, dark mode primary |
| Panel (secondary surface) | `#16171C` | Cards, table zebra striping, sidebar, chat panel |
| Grid Line | `#2A2B33` | Hairline borders on every table and panel — the terminal-grid signature |
| Ink (light mode canvas) | `#FFFFFF` | Light mode background, if enabled |
| Signal Violet (AI accent) | `#6D5EF5` | Agent activity, chat bubbles, primary CTAs — the one color that always means "AI did this" |
| Ledger Blue (data accent) | `#3B82F6` | Links, selected states, financial figures, ticking data |
| Confirm Green | `#1F9D6B` | Won deals, approved status, passed eval checks, upward market movement |
| Caution Amber | `#C98A0A` | Pending review, stalled deals, unresolved risk flags |
| Alert Red | `#D64545` | Lost deals, rejected drafts, overdue items, downward movement |
| Neutral Gray | `#8A8A93` | Disabled states, metadata, timestamps |

### 1.3 Typography

| Role | Typeface | Usage |
|---|---|---|
| UI / body | Inter | Prose, chat, labels — the one warm element against an otherwise dense terminal surface |
| Data / numbers | IBM Plex Mono | Currency, percentages, dates, deal IDs, stage counters — tabular figures, right-aligned, used more heavily than a typical SaaS product to reinforce the trading-terminal register |
| Headings | Inter, Semibold | Section titles, deal names — no separate display face, keeps the system feeling engineered rather than decorated |

### 1.4 Core Interaction Patterns

- **Agent activity indicator** — a small pill component (violet dot + label) that appears anywhere an agent is actively working: "Analyst · summarizing 2 documents…", replacing generic loading spinners system-wide
- **Streaming responses** — chat and document summaries render token-by-token, matching the Orchestrator's conversational persona (Section 4.4 of the system design)
- **Approval gate modal** — any admin action that touches the governance loop (skill update, skill creation, model change) opens the same modal pattern: draft diff on the left, eval pass-rate on the right, single Approve/Reject action

---

## 2. Information Architecture

### 2.1 Navigation Structure

| Element | Detail |
|---|---|
| Top bar | Kuvera logo (left) · global search (center) · Orchestrator chat launcher + user avatar (right). Persistent across all screens. |
| Left sidebar | Dashboard · Deals · Documents & Contracts · Agent Hub · Admin (visible to Admin role only) · collapsed to icons on narrower viewports |
| Main content | Screen-specific — see Section 3 |
| Chat panel | Slide-out from the right, triggered from the top bar or contextually from any deal page; persists across navigation so a conversation with the Orchestrator is never lost when the user clicks elsewhere |

### 2.2 Screens Covered

| Screen | Primary Agent(s) Behind It | Maps to Business Requirement |
|---|---|---|
| Deal Dashboard | Concierge (2.2), Analyst (3.2) | Req 2 — single dashboard for all active deals |
| Deal Detail | Concierge, Analyst, Contracts, Knowledge Agent, Learning Agent | Req 2 — full deal lifecycle record + industry/company knowledge |
| Chat Interface | Orchestrator (persona) | Req 1 — AI Employee |
| Documents & Contracts | Contracts Lead (4.1–4.3) | Req 4 — contract & document management |
| Agent Hub | All agents — read-only monitoring surface | Not a named business requirement, but required to make a 21-agent system operationally trustworthy |
| Admin & Skill Governance | Section 11 governance loop, Knowledge Agent | System configuration — required for the governance model to be usable |

---

## 3. Screen Specifications

### 3.1 Deal Dashboard

Purpose: management's single view of every active deal — the direct answer to "what is the status of every deal right now."

| Element | Detail |
|---|---|
| Header row | Page title "Deals" · view toggle (Board / Table / Pipeline) · New Deal button · filter bar (stage, industry, owner) |
| Pipeline funnel strip | New — a horizontal funnel/bar showing deal count at each of the 7 M&A stages across the whole portfolio, terminal-style (monospace counts, hairline dividers between stages). Clicking a stage segment filters the board/table below to that stage. |
| Board view | Kanban columns, one per deal stage; each card shows deal name, client, assigned owner avatar, a compact risk-flag count badge, and a per-deal Stage Diagram (see below) instead of a plain badge |
| Table view | Dense rows: Deal name, Client, Industry, Stage Diagram (inline, compact), Owner, Documents pending, Overall status, Last activity |
| Right rail (optional) | "Needs attention" panel — deals stalled beyond a threshold or with unresolved high-severity risk flags, generated automatically, not manually curated |

**Per-deal Stage Diagram**

Every deal, wherever it appears (card, table row, or Deal Detail header), carries the same Stage Diagram component — a full-width 7-segment stepper for Lead → NDA → Sourcing & Screening → Valuation & Bidding → Strategy & Preparation → Due Diligence → Negotiation & Closing. The current stage segment is filled Signal Violet; completed stages are filled Grid Line gray with a small checkmark; future stages are outlined only. Hovering or tapping any segment reveals the date the deal entered that stage and how many days it spent there — this is what makes "stalled" visually obvious without reading a table cell.

**Key components**

- **Stage Diagram** — described above; compact variant (dots only, no labels) used in table rows, full variant (labels + hover detail) used on cards and Deal Detail
- **Pipeline funnel** — aggregate stage counts across the portfolio, the dashboard's answer to "where is the bottleneck right now"
- **Status rollup** — a single-word chip (On track / Needs attention / Stalled) computed from Concierge tracking + Risk flagger output, never manually set
- **Empty state** — first-run dashboard shows a prompt to create the first deal or import from a spreadsheet, not a blank table

### 3.2 Deal Detail

Purpose: everything the schema in the system design doc (Section 3.1) captures for one deal, laid out for a human to scan — this is the "Deal A" example made real. Clicking into a deal from the dashboard lands here.

| Element | Detail |
|---|---|
| Header | Deal name, client, industry tag(s), full Stage Diagram (Section 3.1), assigned owner — editable inline |
| Tab: Overview | Overall status, milestone timeline, external contacts list (POC), key dates surfaced by Contracts Lead 4.3 |
| Tab: Documents | Required-documents checklist (received / pending / under review) with AI-generated summary preview per document, powered by Analyst 3.1 |
| Tab: Industries | New — see dedicated breakdown below |
| Tab: Company | New — see dedicated breakdown below |
| Tab: Analysis | Risk flags (3.2) grouped by severity, IC memo draft (3.3) with a "regenerate" action, indicative pricing (3.4) shown collapsed/secondary |
| Tab: Tasks & Notes | Pending task list with owner/due date, meeting notes feed (chronological, AI-summarized per entry) |
| Persistent side panel | "Ask about this deal" — a scoped chat input that opens the Orchestrator panel already primed with this deal's context |

**Tab: Industries**

A deal can span more than one industry (e.g. a healthcare-technology target touches both Healthcare and Software) — each is a sub-tab within Industries, backed by the Industry Insight portion of the Knowledge Agent schema and kept current by the Learning Agent.

| Element | Detail |
|---|---|
| Industry sub-tabs | One per relevant industry tag on this deal; each sub-tab below repeats the same layout |
| Trend cards | One card per identified trend: trend title, Agent's analysis paragraph (from Learning Agent / Industry Brief), a "Sources" row of clickable citation links (opens the original news/article in a new tab), and a "Last updated" timestamp in the card footer |
| Source Library (NotebookLM-style) | A grid of source cards below the trends — one per ingested file (PDF, audio, image, video), each showing a type icon, filename, a one-line AI-generated summary, and duration/page-count metadata; clicking opens an inline viewer/player without leaving the page, matching NotebookLM's source-panel pattern |
| Mindmap view | A toggle (List / Mindmap) at the top of the Industries tab switches the same content into a node-link diagram: a central "[Industry name]" node branches to Trends, Key Players, Regulatory Factors, and Market Sizing nodes, each expandable to reveal the underlying trend cards — a visual entry point into the same data, not a separate dataset |

**Tab: Company**

Backed by the Company Insight portion of the Knowledge Agent schema — retrieved fresh via RAG, since company-specific information changes faster than industry-level trends.

| Element | Detail |
|---|---|
| Company header | Legal name, founding year, HQ location, employee count band — the Deal Profile fields at a glance |
| History | Chronological company history feed, AI-summarized from ingested sources |
| Company news | Reverse-chronological news feed, same card pattern as Industry trend cards (Agent analysis + clickable source links + last-updated timestamp) |
| Competitors | A comparison table — competitor name, relative size, recent competitive actions — sourced from the Competitor Insight schema field |
| Financial statements & data | Multi-year financial summary table (revenue, margin, growth) in IBM Plex Mono figures, with an "Open full statement" link into the Documents tab for the underlying filed PDF |
| Source Library (NotebookLM-style) | Identical pattern to the Industries tab — PDF/audio/image/video sources with AI one-line summaries and inline viewer |
| Mindmap view | Same List / Mindmap toggle — central "[Company name]" node branching to History, News, Competitors, and Financials |

**Key components introduced here**

- **Source card (NotebookLM-style)** — the one recurring component for any ingested file across Industries, Company, and Documents & Contracts: type icon (PDF/audio/image/video), filename, one-line AI summary, metadata, click-to-open inline
- **Mindmap node** — expandable circular node, Signal Violet border for the central topic, Grid Line gray for branch nodes, click-to-expand rather than a static image so large knowledge sets stay navigable
- **Last-updated stamp** — a small monospace timestamp + "refreshed by Learning Agent" label, present on every Trend card, Company section, and Source Library, so a user always knows whether they're looking at this morning's Brief or a stale one

**Worked example — Deal A as it appears on screen**

| Field | Displayed as |
|---|---|
| Contact: Khun A | POC card in Overview tab, with last-contacted date |
| Request FY2025 audited financial statements | Row in Documents checklist, status = "Requested", amber |
| NDA signed | Milestone marker filled on the timeline |
| Due diligence ongoing | Stage badge = "Due Diligence", 5th of 7 segments filled |
| Financial model pending | Task in Tasks tab, unassigned-if-empty state styled distinctly |
| Valuation under review | Analysis tab, Pricing section shown with "In progress" label, not a number yet |

### 3.3 Chat Interface (Orchestrator)

Purpose: the single conversational surface the user ever talks to — per the Orchestrator-as-Personal-Secretary model, Concierge and other Leads never appear as separate chat participants.

| Element | Detail |
|---|---|
| Panel header | "Kuvera Assistant" — no agent-hierarchy language exposed here, deliberately; a small overflow menu offers "View agent activity" for users who want the trace |
| Message thread | Standard chat bubbles; Orchestrator messages in Canvas with a violet left-border accent; user messages right-aligned, neutral |
| Inline artifacts | When a Lead produces a document/deck/summary, it renders as an inline card in the thread (title, type icon, "Open" button) rather than a wall of text |
| Agent activity trace (expandable) | Collapsed by default; expanding shows the actual dispatch path ("Routed to Analyst Lead → 3.1 → 3.2") for users who want transparency — power-user feature, not default noise |
| Composer | Text input, file-attach (routes to Receiver tier 1.3), deal-context chip showing which deal the conversation is scoped to, with an easy way to change or clear it |

### 3.4 Documents & Contracts

Purpose: upload, search, and manage contracts and documents across all deals — Contracts Lead's surface.

| Element | Detail |
|---|---|
| Header | Search bar (semantic search via pgvector, not just filename match) · Upload button · filter by deal / document type / approval status |
| Document list | Table: name, deal, type, uploaded date, AI summary (one-line, expandable), approval status chip, key dates (expiry/renewal) with a countdown badge when within 30 days |
| Document detail (side panel) | Full AI summary (4.1), extracted key clauses as a labeled list (4.2), approval status with change history, related deal link |
| Notifications strip | Persistent banner-style list of upcoming key dates surfaced by 4.3, dismissible per item, not per session |

### 3.5 Agent Hub

Purpose: a read-only, live monitoring surface for all 21 agents — makes a multi-agent system operationally legible instead of a black box, for admins and curious power users alike.

| Element | Detail |
|---|---|
| Agent grid | One card per agent (Orchestrator, every sub-agent 1.1–5.2, Knowledge Agent, Learning Agent), grouped by Lead; each card shows a live status dot (idle / active / error, same visual language as the Agent activity pill), current model_id, and current task if active |
| Agent detail (click-through) | Recent activity log for that agent (timestamped, most recent first), its linked skill.md version, its model_id with a change link (routes to Admin approval queue), and a small sparkline of task volume over the last 7 days |
| Live graph view (toggle) | An alternative view rendering the actual LangGraph structure (matching Figure 1–Figure 8 in the system design doc) with the currently active node(s) highlighted in Signal Violet in real time — the operational counterpart to the architecture diagrams |
| Filter bar | By Lead, by status (show only active / show only errors), by model provider |

**Key components**

- **Live status dot** — pulses while active, solid when idle, red ring on error — the same visual primitive as the chat panel's Agent activity pill, reused here as the anchor of the whole page
- **Error state** — an agent in error shows its last failure reason inline on the card (matching the system design's per-agent "If It Fails" behavior) with a retry action for admins

### 3.6 Admin & Skill Governance

Purpose: makes the governance loop (system design Section 11) actually usable by a human admin, not just a backend process.

| Element | Detail |
|---|---|
| Tab: Skills | List of all 11 skill files (9 task skills + 2 meta-skills), current version, last updated, and a "Pending approval" badge count. A "New Skill" button opens the editor below. |
| Skill editor / upload | New — a split view: markdown editor on the left (or a drag-and-drop zone to upload an existing .md file) and a live rendered preview on the right; submitting sends the draft into the same governance queue as an auto-generated skill_self_update/skill_self_creation draft — human-authored and agent-authored skills go through one identical review path |
| Tab: Pending Approvals | Queue of draft skill/model changes awaiting review — each row opens the Approval gate modal (Section 1.4) showing the diff and eval pass-rate before Approve/Reject |
| Tab: Agents & Models | Table of every agent with its current model_id (Claude / OpenAI / Gemini), editable per agent, changes routed through the same approval queue |
| Tab: Knowledge Base | New — browsable, searchable view into what the Knowledge Agent has actually promoted: filter by industry/outcome/deal, click a record to see its full nested schema (Deal Profile, Insight, Evaluation Approach, Outcome, Risk Signals) exactly as structured in the system design doc's Section 10.1 |
| Tab: Audit Log | Chronological, filterable record of every approved change — who approved, when, and the eval pass-rate at the time |

**Key components**

- **Eval pass-rate bar** — a simple horizontal bar (green above threshold, red below) shown on every pending approval row so an admin never has to open the modal just to triage
- **Diff view** — draft skill.md changes shown as a standard added/removed line diff, familiar to anyone who has reviewed a pull request
- **KB record card** — reuses the same nested-schema layout as the Deal Detail Industries/Company tabs, so a promoted Knowledge Base entry looks visually consistent with the live deal data it was derived from

---

## 4. Component Library

### 4.1 Core Components

| Component | Notes |
|---|---|
| Stage badge | 7-segment bar, filled up to current M&A stage, Signal Violet fill |
| Status chip | On track (green) / Needs attention (amber) / Stalled (red) / Closed (gray) |
| Data table | Zebra-striped rows (Slate), monospace figures, sortable headers, sticky header on scroll |
| Card | Slate surface, 8px radius, used for deal cards, document cards, inline chat artifacts |
| Timeline | Horizontal for deal milestones on Deal Detail; vertical for meeting notes / audit log feeds |

### 4.2 AI-Specific Components

| Component | Notes |
|---|---|
| Agent activity pill | Violet dot (animated pulse while active) + agent name + short action — the one recurring visual signature of "AI is doing something right now" |
| Confidence / error indicator | Small inline badge next to any AI-generated figure or claim, tied directly to the Correctness/Accuracy/Error framework (system design Section 12.1) — not decorative, reflects the actual evaluation |
| Approval gate modal | Standard shell reused for skill update, skill creation, and model-change approvals — diff/summary left, eval result right, Approve/Reject footer |
| Risk flag card | Severity-colored left border (amber/red), one-line description, source citation, and a dismiss/resolve action that feeds back into the Data-Driven Readiness Evaluation as labeled outcome data |

---

## 5. Responsive & Platform Notes

- Primary platform: desktop web (1440px+) — this is an internal operations tool used at a desk, not a mobile-first consumer product
- Tablet (768–1024px): sidebar collapses to icons, Board view remains usable, Table view gains horizontal scroll
- Mobile: out of scope for the MVP demo; the chat interface alone (Section 3.3) is the one screen that would be prioritized first if mobile is added later, since "ask the AI employee a quick question" is the most mobile-natural use case

---

## 6. Accessibility Notes

- Color is never the only signal — every status chip and risk-severity indicator pairs color with a text label or icon
- All agent activity indicators have a text equivalent for screen readers (the pill's label text, not just the pulsing dot)
- Minimum contrast ratio 4.5:1 maintained between Ink/Canvas and all text-on-color combinations in the palette above
