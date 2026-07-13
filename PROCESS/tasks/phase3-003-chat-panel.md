Scope: frontend/src/components/chat/
Depends on: phase1-001 (design tokens, done)
Files allowed to touch: frontend/src/components/chat/*, frontend/src/App.tsx (verification harness only)
DoD:
  - [x] ChatMessage — assistant variant (Panel bg, violet left-border) vs user variant (right-aligned, neutral bg) per ux-ui-spec.md Section 3.3
  - [x] ChatArtifactCard — inline card for Lead-produced documents/decks/summaries (title, type icon, Open button)
  - [x] AgentActivityPill — violet pulsing dot + label, the recurring "AI is doing something" signature (ux-ui-spec.md Section 4.2)
  - [x] ChatComposer — text input, file-attach, deal-context chip
  - [x] ChatPanel — assembles the above: header "Kuvera Assistant" (no agent-hierarchy language exposed, per spec), message thread, collapsed-by-default agent activity trace, composer
  - [x] Single persona only — no Lead tabs (the mockup shows Concierge/Analyst/Contracts/Drafting tabs, but ux-ui-spec.md Section 3.3 explicitly says agent-hierarchy language is deliberately not exposed; the written spec wins per AGENT.md Section 3's "mockup is a reference, converted deliberately")
  - [x] Renders correctly in a real browser with hardcoded sample messages (timeline Phase 3 checkpoint), zero console errors — screenshot confirmed against a running backend-fed Dashboard too
