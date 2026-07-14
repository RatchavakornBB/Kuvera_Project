## Result: 🔶 Code fix complete and verified where possible — full live round-trip blocked by exhausted Anthropic API credits (external, not a code defect)

Gate: root cause confirmed with real data (not assumed) ✅ · a second related bug found and fixed
while investigating the first ✅ · new deep-link verified independently of the blocked API ✅ ·
live chat round-trip blocked by a real account-level constraint 🔶.

User reported the Chat assistant's analysis response looked cut off ("...co...") and asked whether
there's a token limit on the returned output. Investigated with real data rather than assuming:
pulled the actual stored `summary` column directly from the DB for the exact document the user was
looking at — 2575 characters, ending in a complete, well-formed sentence, using roughly 640 tokens
against doc_summarizer's real `max_tokens=1536` ceiling. **The model's own generation was never
truncated.** The cutoff was entirely a hardcoded `result['summary'][:300]` slice in
`backend/app/routes/chat.py`'s `/chat` WebSocket handler — a deliberate short-preview design
(matching `ux-ui-spec.md` 3.3's own stated intent: inline artifacts "rather than a wall of text"),
just cut at an arbitrary character offset instead of a clean boundary.

**Investigating that surfaced a second, more serious bug**: the response's `artifact` object was
meant to be the actual path to the full content — a card with an "Open" button — but it carried no
`deal_id`, and `ChatPage.tsx` (built fresh in phase7-001) never wired an `onOpen` handler onto
`<ChatArtifactCard>` at all. The button rendered, looked clickable, and did nothing. This is worse
than the truncation itself: the user had no way to reach the full analysis from chat at all, not
even a degraded one.

**Fixed both, plus added a new capability needed to make "Open" actually go somewhere:**
- `chat.py`: preview now trims to a word boundary and explicitly tells the user to open the
  artifact for the complete summary/risk flags/IC memo/pricing note; the artifact now carries
  `deal_id`.
- `ChatArtifactCard.tsx` / `ChatPage.tsx`: `onOpen` now navigates to `/deals/{deal_id}?tab=analysis`
  when a `deal_id` is present.
- `DealDetail.tsx`: gained real `?tab=` deep-linking via `useSearchParams` — previously the active
  tab was always local-only state defaulting to Overview regardless of how the page was reached.
  This is a genuinely new, real capability (not previously supported anywhere), not a cosmetic
  tweak.

**Verification was cut short by a real external blocker, disclosed rather than worked around**: the
live Playwright test that sends an actual chat message and waits for a real `analyst_lead` response
failed with a real Anthropic API error — *"Your credit balance is too low to access the Anthropic
API. Please go to Plans & Billing to upgrade or purchase credits."* This blocks every real
Claude-backed feature in the app right now, not just this fix — flagged to the user immediately and
clearly rather than silently retrying or fabricating a passing result. Everything verifiable
without a live Claude call was verified: `tsc --noEmit` clean, backend imports cleanly, and — most
importantly — the new `?tab=analysis` deep-link itself was independently confirmed via a real
browser navigation (no API call involved) landing correctly on the Analysis tab with real
contradiction/risk-flag content visible, proving the navigation half of the fix works. The
remaining check (the actual chat-button click path end to end) needs API credits restored to
finish.

Open item: re-run the full live chat round-trip (send message → get analyst_lead response → click
Open → confirm landing on Analysis tab) once Anthropic API credits are available again.
