# KUVERA CAPITAL — AI Operating Platform: Deal Management & Digital Employee

System Architecture & Agent Design — MVP Proposal
v1.0 | Confidential | Interview Submission

---

## 1. Background & Motivation

### 1.1 Context

Kuvera Capital runs advisory-style deal work — sourcing, due diligence, valuation, and deal execution — the way many lean advisory teams do: information scattered across email threads, shared drives, and individual analysts' heads. There's no single place that answers "what is the status of every active deal right now," and no system that reduces the manual load of digesting due-diligence documents, tracking open items, or drafting investment committee materials.

### 1.2 Problem Statement

- **No centralized deal record** — client info, documents, tasks, and meeting notes live in separate places, so no one has a single view of a deal's true status or diligence progress.
- **Heavy manual document/data review** — financial statements, data-room documents, and contracts are read and summarized by hand for every deal, consuming analyst time that should go to judgment and analysis, not transcription.
- **No institutional knowledge reuse** — the analysis approach, risk patterns, and industry insight built up on past deals are not captured anywhere reusable; every new deal starts its research from a blank page.
- **No proactive tracking** — due-diligence gaps, contract dates, and pending items are easy to miss without a system that watches them and flags gaps automatically.

### 1.3 Why an AI Employee, Not Just a Database

A deal database alone solves visibility but not workload. Kuvera's brief specifically asks for a platform that behaves like a digital employee — one that reads documents, tracks progress, drafts materials, and flags risks without being asked each time. That requires an agentic AI layer sitting on top of the deal database, not a chatbot bolted onto a CRM.

### 1.4 MVP Scope & Roadmap

| Phase | Scope | Goal |
|---|---|---|
| Phase 1 — MVP (this proposal) | Deal DB core, Receiver intake, Concierge + Analyst + Contracts + Drafting leads, LLM Orchestrator | Prove the core loop: intake → analysis → output, on real deal documents |
| Phase 2 — Knowledge layer | Knowledge Agent, semantic memory promotion, pattern-based pricing suggestions | Turn closed deals into reusable institutional memory |
| Phase 3 — Scale & governance | Full RBAC, audit trail maturity, model swap governance, multi-team deal walls | Support multiple deal teams with confidentiality boundaries |

---

## 2. System Overview

### 2.1 Key Statistics

| Metric | Value |
|---|---|
| Total agents / nodes | 21 (1 Orchestrator + 3 Receiver + 11 sub-agents across 4 Leads + Knowledge Agent + Learning Agent + 4 Lead subgraphs) |
| Deal database models | 8 core models (Deal, Contact, Document, Task, MeetingNote, DDItem, Milestone, User) |
| Orchestration framework | LangGraph (Python) — nodes, subgraphs, conditional edges |
| Memory backend | Supabase Postgres (checkpointer, episodic + KG-as-JSONB, storage, auth) |
| AI core | Claude API, OpenAI, Gemini — swappable per agent via model_id |
| Dedicated tools | 5 Receiver normalization tools + 5 Analyst research/reading tools |
| Skill files | 11 (9 task skills + skill-self-update + skill-self-creation meta-skills), all admin-governed |
| Background agents | Knowledge Agent + Learning Agent (continuous market/legal/financial learning) |

### 2.2 High-Level Architecture

- **Frontend:** React (Vite) — deal dashboard, chat interface, document viewer
- **Backend:** FastAPI (Python) — REST + WebSocket, hosts the LangGraph runtime
- **Orchestration:** LangGraph — Orchestrator is an LLM-driven conditional edge; Leads are subgraphs; sub-agents are nodes; deterministic gates enforced by graph edges, not LLM judgment
- **Database & memory:** Supabase — Postgres for deal records and LangGraph Checkpointer, Storage for documents/voice/video, Auth for RBAC
- **AI:** Anthropic Claude API for all reasoning agents (summarization, drafting, risk analysis, routing)

**Figure 1** — Full system overview: Receiver tier → Orchestrator (with Concierge hidden alongside it) → three visible Leads → Background & memory layer. Detailed layer-by-layer explanation in Section 4.2.

### 2.3 User Roles

| Role | Access Level |
|---|---|
| Partner | Full visibility across all deals; approves IC memos and pricing |
| Deal Lead | Full access to assigned deals; assigns tasks; reviews AI output |
| Analyst | Works within assigned deals; uploads documents; uses the AI employee |
| Admin | System configuration, agent model management, user management |
| Viewer | Read-only access — for stakeholders needing visibility only |

---

## 3. Deal Management Database

### 3.1 Schema Overview

| Model | Captures |
|---|---|
| Deal | Deal name, client, industry, stage, assigned team member, overall status, timeline |
| Contact | External contacts — name, role, company, communication history |
| Document | Required/uploaded documents — type, version, upload date, linked deal |
| Task | Pending tasks — owner, due date, status, linked deal |
| MeetingNote | Meeting notes — date, attendees, summary, action items |
| DDItem | Due diligence checklist — item, status (pending/received/reviewed), owner |
| Milestone | Timeline milestones — NDA signed, DD complete, IC approval, closing |
| User | Team members — role, assigned deals, permissions |

### 3.2 Deal Stages

Lead → NDA → Sourcing & Screening → Valuation & Bidding → Strategy & Preparation → Due Diligence → Negotiation & Closing. Each stage transition is logged, and the Concierge Lead's deal tracker sub-agent (2.2) surfaces stalled deals automatically.

| Stage | What Happens |
|---|---|
| Lead | Initial identification of a target or opportunity; not yet qualified |
| NDA | Confidentiality agreement executed before any non-public information is shared |
| Sourcing & Screening | Target research, financial/background verification, initial fit assessment |
| Valuation & Bidding | Financial modeling, indicative valuation range, bid submission |
| Strategy & Preparation | Deal thesis, negotiation strategy, and internal alignment before engaging further |
| Due Diligence | Financial, legal, and operational review; document collection and analysis |
| Negotiation & Closing | Terms finalized, definitive agreements signed, deal closes (won) or falls through (lost) |

### 3.3 Worked Example — Deal A

| Field | Value |
|---|---|
| Deal name | Deal A |
| Contact | Khun A |
| Stage | Due diligence — ongoing |
| Documents | FY2025 audited financial statements — requested |
| Milestone | NDA signed |
| Pending tasks | Financial model — pending; Valuation — under review |

This is exactly the shape the Analyst Lead operates on: once the FY2025 statements arrive, 3.1 summarizes them, 3.2 flags what's still missing (e.g. no cap table yet), and the deal's status card updates automatically on the dashboard via the Concierge Lead.

### 3.4 Dashboard

A single management view lists every active deal, its stage, assigned owner, and a rolled-up status generated by the Concierge Lead (2.2) and the Analyst Lead's risk flagger (3.2) — so a partner can see, at a glance, which deals need attention without opening each one.

---

## 4. AI Employee — Agent Architecture

### 4.1 Why a Hierarchical Multi-Agent System

A single agent with many tools becomes hard to reason about and hard to evaluate once it is doing research, drafting, and notifications all at once. Splitting work into a Lead per business function (Concierge, Analyst, Contracts, Drafting), each with narrow sub-agents, keeps every node's job small enough to test independently — while an LLM-based Orchestrator handles the genuinely ambiguous routing decisions that a fixed rules engine cannot.

### 4.2 Agent Roster

| Tier | Agent | Role |
|---|---|---|
| 0 | Orchestrator | LLM-based router (LangGraph conditional edge); entry router + exception handler, not a mandatory relay for every hop |
| 1 | Receiver (1.1–1.3) | Always-on intake — email, chatbot, multi-modal upload |
| 1 | Concierge Lead | Daily AI-employee interface — Q&A, next actions, tracking, reminders |
| 1 | Analyst Lead | AI deal analysis — summarize, flag risk, draft IC memo, price |
| 1 | Contracts Lead | Contract & document management — summarize, extract clauses, track dates |
| 1 | Drafting Lead | Output production — documents, emails, presentations |
| Background | Knowledge Agent | Promotes closed-deal outcomes into firm-wide semantic memory |
| Background | Learning Agent | Continuously ingests M&A, financial-model, market, and legal knowledge; feeds Brief refresh and skill proposals |

**Reading Figure 1 layer by layer**

- **Receiver tier (top row)** — three always-on, deterministic capture agents (1.1 Email, 1.2 Chatbot, 1.3 Upload). None of them reason about content; they normalize whatever arrives into text and hand it onward. This is the only layer that runs regardless of whether a human is actively using the system.
- **Orchestrator + hidden Concierge (second row)** — the Orchestrator is the single node every request passes through first. It is drawn with Concierge tucked beside it, connected by a short dashed line, to show that Concierge is invoked internally (Section 4.4) rather than being a peer the user ever addresses directly — the dashed border throughout the diagram always means "internal, not user-facing," matching the same convention used for Contracts' scheduled notifier in Figure 6.
- **Three visible Leads (third row)** — Analyst, Contracts, and Drafting produce artifacts a human actually opens and reviews (a memo, a contract summary, a slide deck), which is why they are drawn as ordinary solid boxes at the same visual weight as the Orchestrator, not subordinate to it. The Orchestrator dispatches to any of these three directly; they can also hand off to each other without returning to the Orchestrator (the direct edges detailed in Figures 4 and 6).
- **Background & memory layer (dashed container, bottom)** — the two background agents plus Supabase are drawn inside a dashed container specifically because nothing in this row is triggered by a single user request; Knowledge Agent runs on deal-close events, Learning Agent runs on a schedule, and Supabase is always-on infrastructure underneath everything else, not a step in any request's path.

### 4.3 LangGraph Implementation

- Each sub-agent (1.1–5.2) is a LangGraph node.
- Each Lead is a compiled subgraph inserted as a single node in the parent graph.
- Deterministic sequencing is enforced with plain edges and `Send()` fan-out — never left to LLM judgment. Concretely, inside the Analyst Lead: 3.1 (Doc summarizer) reads the uploaded documents first; only once it completes does 3.2 (Risk flagger) run, since flagging gaps requires knowing what the summary already covers; only once 3.2 completes do 3.3 (IC memo drafter) and 3.4 (Pricing advisor) run — in parallel with each other, since both consume the same completed summary-plus-risk-flags but produce independent outputs. See Section 7 for the full sub-agent definitions and Figure 4 for the diagram.
- The Orchestrator's routing step is a conditional edge whose routing function is itself an LLM call.
- Supabase Postgres serves as the LangGraph Checkpointer, persisting full state after every node — this is both the episodic memory and the audit log.
- Edges are hybrid: most hops are direct node-to-node handoffs (e.g. Analyst's completed memo → Drafting Lead) that never touch the Orchestrator; the Orchestrator is invoked only at entry and at genuinely ambiguous or cross-Lead decision points.

### 4.4 Orchestrator as Personal Secretary

The Orchestrator carries two responsibilities in one LangGraph node, not two separate layers:

- **Persona layer** — every message the user sends or receives goes through the Orchestrator. It is the one consistent "voice" of the AI employee, the way a real personal secretary is the one person you talk to even though they delegate work behind the scenes. It maintains conversational context across turns via the Checkpointer, so the user never has to re-explain which deal they mean.
- **Dispatch layer** — behind that same conversation, the Orchestrator makes the LLM-based routing decision (which Lead, or combination of Leads, should handle this), collects the result, and composes the reply back in its persona voice.

Concierge Lead's two sub-agents (2.1 Q&A + next-action, 2.2 Deal tracker) are called internally by the Orchestrator and never exposed to the user directly — the user sees a single coherent assistant, not a hand-off between agents. Analyst, Contracts, and Drafting remain visible as named Leads in the architecture because their outputs (documents, decks, contract summaries) are artifacts the user reviews directly, whereas Concierge's output is conversational and folds into the Orchestrator's own reply.

---

## 5. Receiver Tier — Multi-Modal Intake

The Receiver tier is deterministic capture, not reasoning — it normalizes every inbound channel into text before anything reaches an LLM agent.

| Sub-agent | Function | Technology |
|---|---|---|
| 1.1 Email intake | Inbound email — parse sender, attachments, body | SendGrid inbound parse |
| 1.2 Chatbot intake | Web widget capture; can send simple acks itself, but real answers come from Concierge 2.1 | WebSocket / FastAPI |
| 1.3 Upload handler | Normalizes voice (STT), PDF, image (OCR), video (transcript + key frames) | Deepgram STT, OCR, PDF text extraction |

**Receiver's 5 tools — deterministic capture, not interpretation**

| Tool | Function | How it differs from Analyst's tools |
|---|---|---|
| Email parser | Extracts sender, attachments, body from SendGrid webhook | Parses structure only, does not read content analytically |
| Chat capture | Logs web widget messages, sends acks | Records the session; does not answer |
| Document normalizer | PDF/DOC/Excel → raw text | Extracts text only; Analyst's File reader interprets tables and figures |
| Voice normalizer | Speech-to-text → raw transcript | Transcribes only; Analyst's Audio tool summarizes meaning and context |
| Visual normalizer | OCR on images; transcript + key-frame extraction on video | Converts to raw text/frames; Analyst's Image/Video tools analyze and summarize |

The dividing line: Receiver tools convert input into raw text deterministically, with no LLM interpretation. Analyst's tools (Section 7.4) read that text and understand it. The same file may pass through both — arriving via an inbound channel (Receiver normalizes it first) — or Analyst may use its own tools directly on something it finds mid-task (e.g. a PDF surfaced by its own web search), without ever touching the Receiver tier.

**Figure 2** — Hybrid routing: obvious cases are hard-routed by a static lookup table; ambiguous or cross-Lead cases go through the LLM Orchestrator.

**Examples of hard-routed cases**

- Email with a PDF attachment matching a known document type (financial statement, NDA, term sheet) → Analyst Lead 3.1
- Email from a tagged contract counterparty with "signed"/"executed" in the subject → Contracts Lead 4.1
- Upload tagged directly into a deal's Contracts folder → Contracts Lead 4.1
- A UI button click ("Summarize this deal's docs") — the action itself encodes intent → Analyst Lead 3.1

Anything requiring interpretation of free-form language, or that could plausibly belong to more than one Lead, goes to the Orchestrator. Hard-routes stay a static lookup table (file type / sender / UI action → Lead) — if a pattern needs more than a simple match, it becomes an LLM-routed case instead.

---

## 6. Concierge Lead

Concierge is not user-facing. Its two sub-agents are called internally by the Orchestrator (see Section 4.4) and their output is folded into the Orchestrator's own reply — the user experiences one consistent assistant, never a hand-off between agents.

| Sub-agent | Function |
|---|---|
| 2.1 Q&A + next-action | Answers questions using company data; recommends next actions |
| 2.2 Deal tracker | Tracks deal progress; creates tasks and reminders |

**Figure 3** — Concierge Lead: parallel sub-agents both write to the live deal dashboard.

---

## 7. Analyst Lead — AI Deal Analysis

| Sub-agent | Function |
|---|---|
| 3.1 Doc summarizer | Summarizes uploaded documents |
| 3.2 Risk flagger | Identifies missing information and highlights key investment risks |
| 3.3 IC memo drafter | Generates an internal investment summary (runs in parallel with 3.4) |
| 3.4 Pricing advisor | Suggests indicative pricing / commercial terms when data supports it (runs in parallel with 3.3) — secondary, best-effort output; risk analysis and the IC memo are the core deliverables |

**Figure 4** — Analyst Lead: sequential gate (3.1 → 3.2) then parallel fan-out (3.3 ∥ 3.4), plus the direct cross-lead edge from Contracts' clause extractor and the direct handoff to Drafting Lead.

**Flow example — document to IC memo**

Financial statements arrive via email or upload → 3.1 summarizes → 3.2 flags missing items (e.g. no audited cash flow statement) → once both complete, 3.3 and 3.4 run in parallel, drafting the IC memo and suggesting indicative pricing → output hands off directly to Drafting Lead for formatting, without returning to the Orchestrator.

### 7.4 Dedicated Toolset

3.1 carries its own tools, kept independent from the Receiver tier's normalization (Section 5.1) — Analyst needs to research and read files on demand mid-task (e.g. a document surfaced by its own web search, or one a user pastes into the conversation), not only what arrived through an inbound channel.

| Tool | Function |
|---|---|
| Web search | Live external research; results feed directly into analysis |
| File reader | Reads and interprets .doc, .xlsx, .pdf — including tables and financial figures |
| Audio | Transcribes and summarizes voice recordings, calls, and meeting audio |
| Image | OCR plus visual summary of scanned pages, charts, and photos |
| Video | Transcript and key-frame summary of recorded meetings and video content |

**Figure 5** — Analyst Lead's dedicated toolset, attached directly to 3.1.

---

## 8. Contracts Lead — Contract & Document Management

| Sub-agent | Function | Trigger |
|---|---|---|
| 4.1 Contract summarizer | Summarizes contract text | On ingest |
| 4.2 Clause extractor | Extracts key clauses | On ingest |
| 4.3 Key-date notifier | Tracks expiry, renewal, and milestone dates | Scheduled background check |

**Figure 6** — Contracts Lead: ingest-triggered pair feeding contract store, a direct cross-lead shortcut into the Analyst Lead's risk flagger, and a separately scheduled key-date notifier.

---

## 9. Drafting Lead

| Sub-agent | Function | Output |
|---|---|---|
| 5.1 Doc/email prep | Formats the IC memo; drafts cover email if going external | .docx, email draft |
| 5.2 Presentation prep | Turns the same content into an IC deck | .pptx |

**Figure 7** — Drafting Lead: dual input (Analyst always, Contracts optional), parallel 5.1/5.2, shared output to storage, and a dashed completion signal back to the Orchestrator.

---

## 10. Background Services — Knowledge & Memory

### 10.1 Knowledge Agent

On deal close, the Knowledge Agent promotes structured patterns — not raw documents — from episodic state into firm-wide semantic memory. Raw documents stay in Supabase Storage; the Knowledge Agent stores summarized, reusable knowledge. This feeds the Risk Flagger (3.2) and Pricing Advisor (3.4) with historical precedent.

**Knowledge schema**

| Category | Contents |
|---|---|
| Deal Profile | Company name & history · industry · company size / valuation · POC (point of contact) |
| Approach / Strategy — Industry Insight | Industry news & actions, trends, financial data (market cap, expansion/contraction), internal & external factors, agent's investment-worthiness and market-growth analysis. Stored as a periodically refreshed "Industry Brief" (see note below), not raw retrieval. |
| Approach / Strategy — Company Insight | Same fields as Industry Insight but company-specific, plus summarized call/meeting/voice/video/file content. Retrieved fresh via RAG on every query — changes too fast to pre-bake. |
| Approach / Strategy — Competitor Insight | Same fields as Company Insight, for named competitors. Structure stored as a Competitor Brief (refreshed periodically); latest actions retrieved via RAG. |
| Evaluation Approach | User decisions (from chat, meeting/call/video summaries), the agent's evaluation methodology for that decision, and user comments on the outcome |
| Analysis Approach | The methodology the agent used to analyze the deal — what data it weighted, what it flagged |
| Strategy Planning Approach | How the strategy was built, combining agent output with user comments and files |
| Outcome | Final M&A result — won / lost, rounds to close, days to close |
| Risk Signals & Resolution | Risks the agent identified during evaluation, and whether each one materialized |
| Prompt Engineering | The system prompts used per agent for this pattern — versioned alongside the outcome they produced |
| Loop Engineering | Which orchestration pattern (gate, fan-out, retry) was used and whether it worked well for this deal type |

**Note on "fine-tuning-style" storage:** Claude does not support public fine-tuning through Anthropic's API. Where the original request calls for industry/competitor knowledge to be "baked in" like a fine-tuned model, this is implemented instead as a periodically regenerated Industry/Competitor Brief — a compact reference document refreshed on a schedule and injected into the relevant agent's context with prompt caching. It behaves like fine-tuned domain knowledge (always present, no retrieval latency) without requiring model weights to be trained.

**How the schema maps to Fine-tuning / Prompt Engineering / RAG**

| Technique | Schema field | Why |
|---|---|---|
| "Fine-tuning" (via Brief, not weights) | Industry Insight, Competitor Insight | Structurally stable, slow-changing — worth pre-baking into context rather than retrieving every time |
| Prompt Engineering | Prompt Engineering field + Skill Markdown (Section 11) | skill.md is the versioned artifact of this technique — governed by the same eval + approve pipeline as any other agent change |
| RAG | Company Insight, Deal Profile, Evaluation/Analysis/Strategy Approach | Changes too fast or is too deal-specific to pre-bake — retrieved fresh via pgvector on every query |

### 10.2 Memory Architecture

| Layer | Purpose | Technology |
|---|---|---|
| Episodic (per-deal state) | Task-scoped state; LangGraph Checkpointer | Supabase Postgres |
| File storage | Documents, voice, images, video from the Receiver tier | Supabase Storage |
| Knowledge graph | Promoted patterns — Company → Industry → Approach → Outcome | Supabase Postgres — JSONB + pgvector (Apache AGE if graph traversal becomes a real need) |
| Auth / RBAC | Role-based access, deal-level confidentiality | Supabase Auth |

### 10.3 Learning Agent

A separate background agent from Knowledge Agent — Knowledge Agent captures patterns from closed deals; Learning Agent continuously ingests the outside world. It runs on a schedule, the same pattern as Contracts Lead's 4.3 Key-date notifier.

**Learns about**

| Learns about | Source |
|---|---|
| M&A training data, deal patterns | Cross-reads Knowledge Agent's promoted records |
| Mathematical prediction models | Academic and financial-modeling literature |
| Business, economic, and stock-market news | Scheduled news / web search ingestion |
| Law and regulation | Legal and regulatory update feeds |

Learning Agent's output feeds two things directly: (1) the Industry/Competitor Brief refresh described in Section 13 (Scale-up Plan) — this is what keeps the "fine-tuning-style" Brief actually current rather than static; and (2) proposed additions to the Skill roster (Section 11), through the `skill_self_creation.md` meta-skill, always subject to the same eval + admin approval gate as any other agent change.

Digests intended for human review — not just machine consumption — route through the existing Drafting Lead rather than a new output pipeline: a NotebookLM-style, source-cited summary via 5.1 (Doc/email prep, scope extended), or a one-page infographic via 5.2 (Presentation prep, scope extended).

---

## 11. Skill Markdown & Governance

Each agent's behavior is tunable through a user-editable Skills field (`skill.md`) — instructions, constraints, or domain knowledge injected into the system prompt at runtime, without touching code. Each agent also holds a `model_id` (Claude, OpenAI, or Gemini) that can be swapped independently of its skill — both go through the same governance loop below.

### 11.1 Skill Roster

| # | Skill | Type |
|---|---|---|
| 1 | Web research | Task skill |
| 2 | Data source evaluation & missing-info identification | Task skill |
| 3 | Financial Analyst & Financial Projection | Task skill |
| 4 | Summary | Task skill |
| 5 | Project evaluation | Task skill |
| 6 | Financial | Task skill |
| 7 | Presentation Creation | Task skill |
| 8 | Risk Analyst | Task skill |
| 9 | Strategy Planning | Task skill |
| 10 | Skill self-update | Meta-skill — governs how skills 1–9 are updated |
| 11 | Skill self-creation | Meta-skill — governs how brand-new skills are proposed, drafted, and added to the roster |

New skills can be added later beyond this starting roster — that is exactly what `skill_self_creation.md` exists to govern.

### 11.2 Skill Governance Loop

Two meta-skills use the same governance pipeline, with different inputs:

- `skill_self_update.md` — the Knowledge Agent's summarized findings (financial analysis, user comments, decision-indicating files) merge with an existing `skill.md` to produce a draft `new_skill.md`, compressed rather than appended so the file doesn't grow unbounded.
- `skill_self_creation.md` — the Learning Agent's continuously ingested knowledge (Section 10.3) surfaces a capability gap not covered by skills 1–9, and drafts a brand-new skill file from scratch.

Both draft types must pass the same governance pipeline as a model change: the eval runner checks the draft against that skill's test cases, and only proceeds to human admin approval (authenticated session, HMAC-signed request, audit log) if the pass-rate threshold is met — a new, untested skill is treated as at least as risky as a small edit to an existing one, not less. Both meta-skills are themselves governed by this same loop; there is no shortcut for changing the rules that govern changes.

**Figure 8** — Skill governance loop, shared by `skill_self_update.md` and `skill_self_creation.md`: draft → eval runner → pass/fail branch → admin approval → commit.

---

## 12. Data-Driven Readiness Evaluation

A quality-check layer that applies across every Lead, not tied to any single one — before a research finding or calculation is promoted into the Knowledge Base, or cited in an IC memo or pricing recommendation, it passes this check.

### 12.1 Framework

Correctness and Accuracy check two different things, not two views of the same thing:

| Dimension | What it checks | Covers |
|---|---|---|
| Correctness | The input — is the source and process sound? | Source of the data · factual correctness · whether the correct process/steps were followed |
| Accuracy | The Agent itself — how precise is its own processing? | Accuracy of the Agent's analysis · accuracy of the prediction model used, including the mathematical formula — its calculation method and its origin/citation |
| Acceptable Error | Statistical margin | The confidence interval / error threshold still considered usable, measured against Accuracy above |

In practice: Correctness is checked once, when data enters the system (is this source and process trustworthy). Accuracy is checked continuously, against the Agent's own track record (has this analysis method / model / formula historically been reliable). A finding can be Correct (good source, sound process) but still fall outside the acceptable Error margin if the Agent's model choice for that scenario has historically been imprecise — the two dimensions are independent and both required before promotion.

### 12.2 Supervised / Unsupervised / Reinforcement Learning — Evaluation Methods per Agent

These are the three methods used to evaluate an individual agent's output — not a separate data-quality system. Supervised evaluation is, concretely, the eval runner from Section 11: it is the default method whenever a ground-truth answer exists.

| Method | How it evaluates an agent | Example |
|---|---|---|
| Supervised | Compares the agent's output against a known-correct answer in an eval file — this is the eval runner (Section 11.2) itself, used for pass/fail regression testing on every skill or model change | 3.2 Risk flagger's output is checked against an eval file listing the risks that should have been flagged for that test case |
| Unsupervised | Used when no ground truth exists yet (e.g. a new industry or scenario) — flags outputs that deviate from established patterns for human review, rather than auto pass/fail | Learning Agent surfaces a source or pattern unlike anything seen before — routed to admin review instead of silently trusted |
| Reinforcement | Evaluates an agent using the real-world outcome of the deal, arriving after the fact as a delayed reward, to adjust future weighting | If 3.4 Pricing advisor's suggestion led to a closed deal, that reasoning pattern is reinforced; if the deal fell through, it's down-weighted for similar future scenarios |

---

## 13. Scale-up Plan

As research volume grows, the priority is that the system stays responsive — the mechanisms below are ordered by when they become necessary, not built all at once in the MVP.

| Mechanism | Solves |
|---|---|
| Tiered retrieval | Most questions answer from the cached Industry/Competitor Brief (fast); only Company Insight — which changes quickly — hits live RAG, keeping pgvector load down as research volume grows |
| Vector index tuning + partitioning | As embeddings grow, use HNSW indexing and partition by industry / deal-vintage to avoid full-table scans |
| Async ingestion queue | Separates "capture and embed" from "answer the user" into different paths — the user isn't blocked waiting for ingestion to finish. This is the concrete trigger for adding Redis (deferred until now per the "add only when needed" principle) as the queue backend |
| Incremental brief regeneration | Learning Agent (Section 10.3) refreshes the Industry/Competitor Brief incrementally rather than rebuilding from scratch each cycle, keeping refresh time flat as raw data grows |
| Parallel research fan-out | Analyst's web search and file-reader tools (Section 7.4) query multiple sources concurrently via LangGraph fan-out rather than sequentially |

**Note on scaling triggers:** the Neo4j migration trigger from Section 10.2 (~500 closed deals) is a different axis from research-data volume — a small number of deals can still carry a very large number of embeddings each. A separate trigger applies to vector storage specifically: consider a dedicated vector store once embeddings exceed roughly 1M vectors, independent of deal count.

---

## 14. Security & Access Control

- Role-based access via Supabase Auth — Partner, Deal Lead, Analyst, Admin, Viewer
- Deal-level confidentiality — analysts see only assigned deals unless elevated to Deal Lead or Partner, supporting Chinese-wall style separation between deal teams
- Full audit log — every node execution is persisted by the LangGraph Checkpointer, giving a complete trace of who/what touched a deal record and when
- Model and skill changes to any agent require an authenticated admin session, and must pass an eval-file regression check before being committed to production

---

## 15. Technology Stack & Deployment

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React (Vite) | Fast to build a deal dashboard and chat UI; proven pattern |
| Backend / API | FastAPI (Python, async) | Native async fits LangGraph; auto-generates OpenAPI docs |
| Orchestration | LangGraph | State machine with Checkpointer for crash recovery and human-in-the-loop resume |
| Database | Supabase Postgres | Checkpointer store, deal records, KG-as-JSONB, pgvector for semantic search |
| File storage | Supabase Storage | Documents, voice, images, video |
| Auth | Supabase Auth | Built-in RBAC — saves build time for an MVP |
| AI core | Claude API, OpenAI, Gemini | Multi-provider by design — each agent holds a model_id, so the model powering it can be swapped without rebuilding the pipeline (Section 11's governance loop applies to model changes too, not just skill changes) |
| Speech-to-text | Deepgram | Multilingual transcription for voice intake |

---

## 16. MVP Deliverable Plan

For the interview prototype, the goal is to demonstrate the core loop end to end on a small, real dataset rather than build every Lead in full:

- Deal Management Database with the schema above, seeded with 2–3 example deals (including the "Deal A" example)
- A working deal dashboard showing stage, status, and pending items
- Receiver → Orchestrator → Analyst Lead working end to end: upload a document, get a summary, risk flags, and a draft IC memo
- Concierge Lead's Q&A sub-agent answering questions against the seeded deal data
- A visible LangGraph trace (via the Checkpointer) so the graph's decisions are inspectable during the demo
- Contracts Lead, Drafting Lead's presentation output, and the Knowledge Agent are designed above and ready to build next, but are secondary to proving the Receiver → Orchestrator → Analyst → Concierge loop actually works on real input.
