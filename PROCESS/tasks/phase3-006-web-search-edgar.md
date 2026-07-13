Scope: agents/tools/sec_edgar.py, agents/nodes/web_research.py, agents/nodes/orchestrator.py (add a 3rd route), backend/app/routes/chat.py (wire the 3rd route)
Depends on: phase3-004-chat-websocket (done — Orchestrator routing pattern established)
Files allowed to touch: files listed above
DoD:
  - [x] web_search added as Anthropic's official server tool (system-architecture.md Section 5.2) — not a custom scraper, citations parsed from the real citations array
  - [x] SEC EDGAR fetcher (Section 5.3) — real two-step call (CIK lookup then filing fetch), compliant User-Agent header, no API key needed, hard-routed as a plain conditional (not an LLM tool-use round trip)
  - [x] Orchestrator gets a 3rd route (web_research) alongside concierge_qa/analyst_lead
  - [x] Verified with real queries via a live WebSocket round trip: "What is Medtronic trading at, recent news?" correctly routed to web_research, returned a detailed, accurate, current answer with 10 real citations. A 10-K/EDGAR-triggering query initially exposed a real bug (see report) — fixed, then re-verified clean with 8 correct citations against the real Medtronic 10-K filing.
