Scope: backend/app/routes/chat.py, frontend/src/components/chat/ChatArtifactCard.tsx,
frontend/src/pages/ChatPage.tsx, frontend/src/pages/DealDetail.tsx
Depends on: phase7-001 (Chat page rebuild), pre-existing AnalysisTab (phase4-001c)

Scope: user reported the Chat assistant's analysis response looked cut off mid-sentence
("...co...") and asked whether there was a token limit on the returned output. Investigated by
reading the actual stored full summary directly from the DB for the exact document in question:
2575 characters, ending in a complete sentence, comfortably under doc_summarizer's real
max_tokens=1536 ceiling (~640 tokens used). This proved the LLM generation itself was NOT
truncated — the cutoff was `backend/app/routes/chat.py`'s hardcoded `result['summary'][:300]`
preview slice in the /chat WebSocket's analyst_lead response. A second, related bug was found
while investigating: the response includes an `artifact` card with an "Open" button meant to show
the full content (matching ux-ui-spec.md 3.3's documented "inline artifacts... rather than a wall
of text" pattern), but the artifact object carried no `deal_id`, and ChatPage.tsx (built in
phase7-001) never wired an `onOpen` handler at all — the button was a real, visible, but
completely non-functional no-op.

DoD:
  - [x] `backend/app/routes/chat.py`: preview now trims to a clean word boundary
        (`.rsplit(" ", 1)[0]`) instead of an arbitrary mid-word character cut, and explicitly tells
        the user to open the artifact for the full content
  - [x] `artifact` dict now includes `deal_id` so the frontend has enough information to navigate
        somewhere real
  - [x] `ChatArtifact` interface (ChatArtifactCard.tsx) gained an optional `deal_id` field
  - [x] `ChatPage.tsx`: wires a real `onOpen` handler that navigates to
        `/deals/{deal_id}?tab=analysis` when the artifact has a `deal_id`
  - [x] `DealDetail.tsx`: reads `?tab=` from the URL via `useSearchParams` to initialize which tab
        is active, validated against the real `DealTab` union — a genuinely new deep-linking
        capability, not previously supported (tab state was always local-only, defaulting to
        Overview no matter how the page was reached)
  - [x] Verified past "no error thrown": `tsc --noEmit` clean, backend imports cleanly. Verified
        the new deep-link independently of any Claude API call (see Blocker below) — direct
        navigation to `/deals/{id}?tab=analysis` correctly landed on the real Analysis tab showing
        real contradiction/risk-flag content, confirmed via a real browser screenshot
  - [x] Full live round-trip through the actual Chat UI (send a message, get the analyst_lead
        response, click Open, confirm landing on Analysis tab) — RESOLVED, see below

Blocker hit during initial verification (external, not a code defect): the real Playwright browser
test sending an actual chat message failed with a real Anthropic API error —
`"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to
upgrade or purchase credits."` The user topped up the account (2026-07-14). Re-ran the full live
round-trip: sent a real message, got a real analyst_lead response with the fixed word-boundary
preview ("...but explicitly excludes… (open the artifact below for the full summary, risk flags,
IC memo, and pricing note)"), clicked the real Open button, and confirmed real navigation to
`/deals/{id}?tab=analysis` landing on the Analysis tab — zero console errors. DoD fully met.
