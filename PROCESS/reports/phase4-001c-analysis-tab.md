## Result: ✅ DoD met

Gate: `npx tsc --noEmit` ✅ · real browser end-to-end test (Playwright, against the real backend and
Supabase, not mocked) ✅.

New backend surface: `GET /deals/{id}/analysis` (`app/routes/analyze.py`, `app/services/analyze.py`)
wraps the existing `agents.analyses.get_last_analysis` helper so the tab can hydrate from the last
stored run without triggering a new (costly, real-API) LLM invocation just to view the page. Loaded
Deal A's Analysis tab and confirmed the real stored analysis rendered immediately: 3 high-severity +
6 medium-severity risk flags, IC memo draft, and the pricing section.

Then clicked Regenerate against the real `/deals/{id}/analyze` endpoint (full LangGraph run — doc
summarizer, risk flagger, IC memo drafter, pricing advisor — took under 3 minutes end to end) and
confirmed the UI updated to a genuinely new result set (high-severity count changed 3 → 1, flag text
changed), not a stale cache. Notably, the "before" run's risk flags included a real hit from the
Phase 2 contradiction-check feature ("Discrepancy between prior and current analysis... narrow
indemnification scope... not identified in the prior stored analysis") — confirms that machinery is
still live and firing correctly, not something I had to construct for this test. Zero console errors
in either pass.

Deviations from spec: none. The spec ties "Regenerate" to the IC memo panel specifically; since
`/analyze` is one atomic graph run that produces the summary + risk flags + IC memo + pricing
together, Regenerate re-runs the whole analysis (updating all three sections), not just the memo
text — there's no partial-regeneration primitive in the backend, and building one would be scope
creep beyond what the spec asks for.

Risks: the document selector defaults to the most recently *uploaded* document, which is not
necessarily the document the currently-displayed stored analysis was run against (the stored
analysis is deal-level "latest by created_at", independent of which document is newest). This is
intentional — the selector's job is "what will Regenerate run against," not "what is displayed" —
but it's worth flagging in case a future reviewer expects those to always match.
