Scope: frontend/src/styles/tokens.css, frontend/src/index.css, frontend/src/components/StageDiagram.tsx, frontend/vite.config.ts, frontend/index.html, frontend/src/App.tsx (verification harness only)
Depends on: none (first frontend components — everything else imports design tokens from here)
Files allowed to touch: everything under frontend/ (fresh scaffold)
DoD:
  - [x] Tailwind v4 wired via @tailwindcss/vite, dark terminal-black background by default
  - [x] Design tokens match UX/UI spec Section 1.2 (color) and 1.3 (typography) exactly
  - [x] StageDiagram renders correctly for a deal at each of the 7 stages, compact + full variant (Section 6 Phase 1 checkpoint)
  - [x] npx tsc --noEmit passes
  - [x] Rendered in a real browser (Playwright screenshot), zero console errors
