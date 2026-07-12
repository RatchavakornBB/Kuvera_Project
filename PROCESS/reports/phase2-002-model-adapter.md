## Result: ✅ DoD met

Gate: manual verification only — a real (not mocked) call through `call_model('doc_summarizer', [...])` reached the live Anthropic API and returned a real response (model `claude-sonnet-5`, correct text, real token usage), proving the API key, the model_id, and the dispatch logic are all actually correct together.

Deviations from spec: `agents/` got its own `config.py` rather than importing `backend/app/config.py` — see D-007. This wasn't in the original task scope-lock but was necessary to make the node standalone-testable as the timeline itself requires; logged as a decision rather than silently expanding scope.

Risks: only the Anthropic provider branch is implemented (`_provider_for` recognizes `gpt-`/`gemini-` prefixes but raises `NotImplementedError` for them) — correct for this week, since only Claude is called, but a real second-provider wire-up will need actual per-provider client + response-shape handling, not just a new branch.
