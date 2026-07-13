Scope: supabase/migrations/<new>_create_contradictions.sql, agents/contradictions.py,
agents/nodes/risk_flagger.py, backend/app/services/contradictions.py,
backend/app/routes/deals.py, frontend/src/lib/api.ts,
frontend/src/components/dealDetail/ContradictionsPanel.tsx,
frontend/src/components/dealDetail/AnalysisTab.tsx
Depends on: phase5-009 (done, provides the pgvector/embeddings infra this reuses)
Files allowed to touch: files listed above

Scope note: 5day-build-timeline.md references "Full Contradiction & Hypothesis confidence-scoring
engine (Section 10.5)" but no such section (or any more detailed spec) exists anywhere in
docs/system-architecture.md — the only real spec is one line: "status ranks, corroboration
counting, versioned promotion into Knowledge Agent." Designed from that description since nothing
more detailed exists to follow; user asked to proceed through the full remaining list without
per-item confirmation.

Design: extends, does not replace, the already-verified-working lightweight contradiction check
in risk_flagger.py (still surfaces an ordinary high-severity risk flag, unchanged). Adds real
structured tracking behind it in a new `contradictions` table: status ranks
(unconfirmed -> corroborated -> resolved/refuted), corroboration counting matched via real
pgvector cosine similarity (the flagged description is freshly LLM-generated on every re-analysis,
never identical wording, so exact-match isn't viable), and a real "resolve" action that promotes a
versioned record into `knowledge_base` (reusing phase5-009's Knowledge Agent).

DoD:
  - [x] `contradictions` table with real GRANTs, HNSW cosine index on `embedding`
  - [x] `RISK_FLAGGER_TOOL` schema extended with `is_contradiction` so the model explicitly marks
        which flag (if any) is the contradiction one — reliable routing, not fragile text parsing
  - [x] `record_contradiction()`: real pgvector similarity search against the deal's existing open
        contradictions; matches increment corroboration and flip status at count >= 2; no match
        inserts a new row. Threshold calibrated against real embeddings (not guessed): a genuine
        paraphrase scored 0.77, an unrelated contradiction scored 0.50 — set to 0.70
  - [x] `resolve_contradiction()`: real status transition + real promotion into `knowledge_base`
        (category `risk_signals_resolution`) on `resolved`, no promotion on `refuted`
  - [x] Backend: `GET /deals/{id}/contradictions`, `POST /deals/{id}/contradictions/{id}/resolve`
  - [x] Frontend: `ContradictionsPanel` on the Analysis tab — status-colored rows, resolve/refute
        action with a note field, hidden entirely when a deal has no contradictions (no empty
        clutter)
  - [x] Verified end to end with real data: real corroboration matching (two paraphrased
        descriptions merged, an unrelated one stayed separate — recalibrated the threshold after
        the first test run showed 0.85 was too strict), real resolve -> real promoted
        knowledge_base row with the correct version number, and a real full `/deals/{id}/analyze`
        run against Deal A (which has prior analyses) to confirm the wiring fires from the actual
        risk_flagger node, not just direct function calls. Also had to raise risk_flagger's
        max_tokens twice (4096 -> 8192 -> 16384) after real live runs kept hitting the ceiling —
        confirmed clean on both the real API and a real browser session with zero console errors.
