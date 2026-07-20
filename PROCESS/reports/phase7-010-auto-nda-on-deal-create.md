# phase7-010 — Auto-NDA on deal create

**Ask (user):** "After create deal — the AI will create the NDA doc for client and put in deal page."

## Result: ✅ DoD met, live-verified

Creating a deal now auto-drafts a mutual NDA (.docx) and drops it into the deal's Documents tab.

### Locked decisions (via AskUserQuestion)
- NDA source: **AI-drafted** (not template).
- Extra effects: **just the document** — stage stays `Lead`, no milestone/task added.
- Owner agent (D-013): **new `nda_drafter` agent**, NOT `drafting_lead`.

### What was built
- `agents/drafting_lead.py`: `NDA_PROMPT`, `_get_deal()` (deal-only fetch — NDA needs no prior
  analysis), `draft_nda()` (real `call_model("nda_drafter", …)`), `draft_nda_docx()` (python-docx
  via the existing `_add_markdown_paragraphs` renderer), `draft_and_store_nda()` (reuses
  `_upload_and_record` → same Storage+Document write path as memo/deck, `type='NDA'`).
- `backend/app/services/deals.py`: `create_deal()` fires `_draft_nda_async()` on a daemon thread —
  best-effort, must never block/hang/fail deal creation (post-model failures print to stderr, not
  swallowed silently; the `call_model` invocation is logged to `agent_invocations` regardless).
- `agents/adapters/model_adapter.py`: added `"nda_drafter": "claude-sonnet-5"` to `AGENT_MODELS`.
- `backend/app/services/drafting.py` + `routes/drafting.py`: manual `POST /deals/{id}/draft/nda`
  (re-draft / verification handle).
- No frontend change: `DealFileLibrary` lists all document types with no filter.

### Real finding (caught during verification)
First verification run went through `call_model("drafting_lead", …)` and the model **refused** —
drafting_lead's governed skill deliberately forbids from-scratch generation, so its refusal text
got stored as the "NDA". The automated marker-check nearly false-passed (the refusal text mentioned
"Non-Disclosure"/the client name). Detected by reading the actual content, surfaced to the user as a
spec/decision gap (AGENT.md §9.3), resolved by moving NDA drafting to a dedicated `nda_drafter`
agent with no restrictive skill. See D-013.

### Verification
- End-to-end through `create_deal()` on a throwaway deal → background NDA landed within poll window:
  real 5.7 KB .docx (PK magic ok), proper numbered NDA sections (Parties, Confidential Information,
  Term, obligations…), self-labeled "preliminary draft for internal review", `[PLACEHOLDER]` markers
  for unknown legal values, **zero refusal markers**. Downloaded from Storage and text-extracted to
  confirm.
- `TestClient`: `POST /deals/{id}/draft/nda` wired (returns `Deal not found` on a fake id, i.e. the
  handler ran — not a route-missing `Not Found`). `GET /deals` 200.
- App imports clean; `nda_drafter` registered.
- Both "ZZ NDA Verify" throwaway test deals cleaned up (deal + document rows + storage objects; 0
  remaining).

### Caveats / not done
- **Not committed** (user commits only when asked).
- The **running uvicorn on :8000 is on old code** — needs a restart to serve the new route and the
  auto-NDA trigger live (the known "restart to pick up changes" gotcha). Verified via direct
  service calls + TestClient, which load current code.
- `nda_drafter` has no `agent_configs` skill row yet (by design) — an admin can attach/version a
  governed NDA skill later via the Admin UI.
- Parallel session added a Gemini adapter to `model_adapter.py` mid-task (unrelated to this) — left
  untouched.
