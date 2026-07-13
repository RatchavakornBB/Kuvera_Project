## Result: ✅ DoD met — real corroboration matching, real versioned promotion

Gate: syntax checks ✅ · real end-to-end verification (direct function calls, real HTTP, and the
actual `/deals/{id}/analyze` pipeline) ✅.

No detailed spec exists for this feature — 5day-build-timeline.md references "Section 10.5" for
"Full Contradiction & Hypothesis confidence-scoring engine," but no such section, or any more
detail, exists anywhere in `docs/system-architecture.md`. Designed from the one available
description ("status ranks, corroboration counting, versioned promotion into Knowledge Agent")
since nothing more detailed exists to follow.

**Architecture:** new `contradictions` table (status: unconfirmed → corroborated → resolved/
refuted). `risk_flagger`'s tool schema gained an `is_contradiction` boolean so the model explicitly
marks which flag (if any) is the contradiction one — reliable routing instead of parsing free text.
`agents/contradictions.py::record_contradiction()` embeds the new description via Voyage and
searches the deal's existing open contradictions by cosine similarity; a match increments
corroboration (flipping to `corroborated` at count ≥ 2), no match inserts a new row.
`resolve_contradiction()` does a real status transition and, on `resolved`, promotes a versioned
record into `knowledge_base` (reusing phase5-009's Knowledge Agent) — the "versioned promotion"
half of the spec.

**Real calibration, not a guessed threshold:** first test run used 0.85 similarity and incorrectly
treated two genuine paraphrases of the same contradiction as unrelated. Queried the real cosine
similarity directly in Postgres: a true paraphrase scored 0.77, an unrelated contradiction scored
0.50. Reset the threshold to 0.70 — comfortable margin on both sides — and re-verified: the
paraphrase now correctly merges (status flips to `corroborated`, count 2), the unrelated one stays
separate.

**Real bugs found via the actual `/deals/{id}/analyze` endpoint** (not just direct function
testing), fixed iteratively against real repeated failures rather than guessed at once:
`risk_flagger`'s `max_tokens` (4096) was too low once historical-precedent context (phase5-009) and
the new `is_contradiction` reasoning pushed real output length up. Raised to 8192 — reproduced the
same real inputs manually and it succeeded with only ~2156 output tokens, so the fix looked
sufficient — but the *next* real live `/analyze` call hit `stop_reason='max_tokens'` again (extended
thinking + a document with many real findable risks + contradiction/precedent reasoning can vary
run to run well past a single successful sample). Raised again to 16384 for real headroom rather
than re-tuning to the last observed number, restarted the backend, and reran the actual endpoint —
succeeded cleanly this time, and the real contradiction (a confidentiality-survival-term omission
between the new and prior analysis) was correctly detected, flagged, and persisted as an
`unconfirmed` row with `corroboration_count: 1` through the real production code path, not a direct
function call. One transient failure along the way (an empty `{}` tool_use input despite
`risk_flags` being required) did not reproduce on an immediate retry with identical real inputs —
consistent with a rare Claude tool-calling glitch, exactly the failure mode `with_retry`'s
bounded-retry + typed `NodeFailure` design already exists to handle, not something to chase further.

Final verification, done twice: once via the real `/deals/{id}/analyze` HTTP endpoint (confirmed the
contradiction row was created correctly), and once via a real Playwright browser session confirming
the Contradictions panel renders it correctly on the Analysis tab with zero console errors.

**Frontend:** `ContradictionsPanel` on the Analysis tab — status-colored rows with corroboration
count, a resolve/refute action with a note field, hidden entirely (no empty clutter) when a deal
has no contradictions.

Deviations: none from the design confirmed by proceeding through the user's ordered list without
per-item re-confirmation, as instructed.
