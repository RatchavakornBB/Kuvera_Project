Scope: frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/components/layout/, frontend/package.json (react-router-dom)
Depends on: phase3-005 (chat panel working)
Files allowed to touch: files listed above
DoD:
  - [x] react-router-dom installed and wired: route for Dashboard (/) live now; Deal Detail/Documents/Agent Hub routes added as their own tasks build them
  - [x] AppShell component: top bar (logo, search placeholder, chat launcher, avatar) + left sidebar nav (Dashboard/Documents & Contracts/Agent Hub — "Deals" not added as a separate item since it's the same screen as Dashboard per ux-ui-spec.md Section 2.2's screen table; Admin excluded, its build-or-design-only status is an open question for the user) per Section 2.1, persistent across all routes
  - [x] Chat panel becomes a slide-out toggled from the top bar (per spec: "triggered from the top bar or contextually... persists across navigation"), not permanently docked — deal context now flows through a ShellContext (askAboutDeal) child pages can call via useOutletContext
  - [x] Existing Dashboard/Chat functionality still works after the refactor — regression-checked in a real browser (screenshot), zero console errors, chat toggle verified open/closed
