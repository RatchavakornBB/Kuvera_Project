## Result: ✅ DoD met — real per-deal document list in the Chat Sources panel

Gate: real document data (no fabrication) ✅ · real browser verification independent of the
Anthropic API outage ✅ · zero console errors ✅.

User asked for the Chat page's Sources panel to show a deal's related documents when clicked into.
Implemented by reusing existing real infrastructure end to end — `fetchDocuments({ deal_id })` and
`documentDownloadUrl()` are the same functions the Documents & Contracts screen and Deal File
Library already use, so no new backend endpoint was needed.

Clicking a Source row now does two things at once: selects the deal as the active chat context
(unchanged prior behavior from phase7-001) and expands a nested list of that deal's real documents
underneath it, each with a real backend-mediated download link. Clicking the same deal again
collapses it. Only the selected deal's documents are ever fetched (`enabled: !!selectedDeal`), not
all deals' documents up front.

**Verified without needing any Claude API call**, which mattered given the account is currently out
of credits (phase7-004): this feature is pure Postgres-backed document listing, no LLM involved.
Real browser test against Deal A showed all 7 of its real documents (IC memo, deck, financial
summary, contract, etc.) with working download links, and confirmed the collapse/expand toggle and
selection state don't interfere with each other. Zero console errors, `tsc --noEmit` clean.

No open deviations.
