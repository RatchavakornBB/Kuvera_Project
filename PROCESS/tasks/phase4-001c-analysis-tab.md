Scope: backend/app/routes/analyze.py, backend/app/services/analyze.py,
frontend/src/lib/api.ts, frontend/src/components/dealDetail/AnalysisTab.tsx,
frontend/src/components/dealDetail/RiskFlagCards.tsx,
frontend/src/components/dealDetail/IcMemoPanel.tsx,
frontend/src/components/dealDetail/PricingSection.tsx,
frontend/src/pages/DealDetail.tsx
Depends on: phase4-001b (done)
Files allowed to touch: files listed above
DoD:
  - [x] GET /deals/{id}/analysis returns the latest stored analysis row (or null) so the tab
        can hydrate without forcing a fresh (costly) LLM run on every page load
  - [x] Risk flags grouped by severity (high first, then medium), matching ux-ui-spec.md
        Section 3.2's "Risk flags grouped by severity"
  - [x] IC memo draft panel with a Regenerate action (re-runs /analyze against the selected
        source document)
  - [x] Pricing section shown collapsed/secondary per spec, with an explicit "In progress"
        state when pricing_note is null (matches the "Valuation under review" state in
        ux-ui-spec.md line 156), and surfaces pricing_error detail if present (never a silent
        generic failure per AGENT.md Section 10)
  - [x] Document selector defaults to the most recently uploaded document when a deal has more
        than one (analyze is per-document, tab is deal-level)
  - [x] Verified end to end in a real browser: load Deal A's Analysis tab (existing stored
        analysis from Phase 2/3 testing should render immediately), then Regenerate and watch
        real risk flags / IC memo update, zero console errors
