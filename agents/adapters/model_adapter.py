"""The only path to any LLM provider — every LangGraph node calls
call_model(), never a provider SDK directly (AGENT.md Section 1 / 11).

Only Claude is actually called this week, but the shape here is what makes
adding a second provider a config change instead of a node rewrite later:
look up agent_name's model_id, dispatch to the client for that model_id's
provider.
"""

from functools import lru_cache

import anthropic

from agents.activity_tracker import finish_invocation, start_invocation
from agents.agent_config import get_agent_config
from agents.config import settings

# Which model_id each agent uses — the only place this is decided.
# Swapping an agent's model is a one-line change here, not a node edit.
AGENT_MODELS: dict[str, str] = {
    "doc_summarizer": "claude-sonnet-5",
    "risk_flagger": "claude-sonnet-5",
    "ic_memo_drafter": "claude-sonnet-5",
    "pricing_advisor": "claude-sonnet-5",
    "contract_summarizer": "claude-sonnet-5",
    "clause_extractor": "claude-sonnet-5",
    "contracts_lead": "claude-sonnet-5",
    "concierge_qa": "claude-sonnet-5",
    "orchestrator": "claude-sonnet-5",
    "knowledge_promoter": "claude-sonnet-5",
    "industry_brief": "claude-sonnet-5",
    "competitor_brief": "claude-sonnet-5",
    "learning_agent": "claude-sonnet-5",
    "drafting_lead": "claude-sonnet-5",
    "company_research": "claude-sonnet-5",
}
DEFAULT_MODEL = "claude-sonnet-5"


def _provider_for(model_id: str) -> str:
    if model_id.startswith("claude-"):
        return "anthropic"
    if model_id.startswith("gpt-"):
        return "openai"
    if model_id.startswith("gemini-"):
        return "google"
    raise ValueError(f"Unrecognized model_id: {model_id}")


# The SDK's own default timeout is generous (10 minutes) with no way for a
# hung network call to fail loud sooner — a real hang was observed live
# (a WebSocket /chat request stuck "thinking" for 5+ minutes with no error,
# no LangGraph checkpoint ever written, while re-running the identical call
# moments later completed cleanly in ~20s). An explicit, tighter timeout
# means a stall converts into a real exception with_retry already knows how
# to handle (bounded retry, then a clean NodeFailure) instead of silently
# blocking a thread-pool worker for up to 10 minutes.
REQUEST_TIMEOUT_SECONDS = 120.0


@lru_cache
def _anthropic_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=REQUEST_TIMEOUT_SECONDS)


def call_model(
    agent_name: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    system: str | None = None,
    max_tokens: int = 4096,
    betas: list[str] | None = None,
    track_invocation: bool = True,
) -> anthropic.types.Message:
    """Dispatches a chat completion for `agent_name` to that agent's
    configured model_id. Returns the provider's native response object —
    single-provider for now, so no normalization layer exists yet
    (add one only once a second provider is actually wired in).

    Looks up `agent_name`'s real, DB-stored config (agent_configs, governed
    through the Admin & Skill Governance approval loop) on every call —
    deliberately not cached across the process lifetime, so an approved
    change is live on the very next call, not after a restart. Falls back
    to the static AGENT_MODELS default only if no DB row exists yet.

    `betas` opts into Anthropic beta-only server tools (e.g. `web_fetch`,
    still beta as of this build) by routing through `client.beta.messages`
    instead of the standard endpoint — omit it for every other call.

    `track_invocation=False` skips the per-call agent_invocations row.
    Used by agents/loop_runner.py: a multi-step agentic loop brackets one
    invocation row around the whole run (start before the loop, finish
    after) instead of one row per API call inside it — otherwise a single
    4-iteration loop would create 4 rows and break the Agent Hub's
    "one row per top-level invocation" semantics. Every existing
    single-shot caller is unaffected (default True)."""

    config = get_agent_config(agent_name)
    model_id = config["model_id"] if config else AGENT_MODELS.get(agent_name, DEFAULT_MODEL)
    skill_content = (config.get("skill_content") or "").strip() if config else ""

    effective_system = f"{skill_content}\n\n{system}" if skill_content and system else skill_content or system

    provider = _provider_for(model_id)
    invocation_id = start_invocation(agent_name) if track_invocation else None

    if provider == "anthropic":
        client = _anthropic_client()
        kwargs: dict = {"model": model_id, "max_tokens": max_tokens, "messages": messages}
        if effective_system:
            # A cache breakpoint on the system prompt only pays off for content
            # that's actually stable call-to-call (skill_content, an Industry
            # Brief) — every existing caller already meets that bar, since none
            # vary `system` per-request today.
            kwargs["system"] = [
                {"type": "text", "text": effective_system, "cache_control": {"type": "ephemeral"}}
            ]
        if tools:
            kwargs["tools"] = tools
        try:
            if betas:
                response = client.beta.messages.create(betas=betas, **kwargs)
            else:
                response = client.messages.create(**kwargs)
        except Exception as e:
            if track_invocation:
                finish_invocation(invocation_id, "error", str(e))
            raise
        if track_invocation:
            finish_invocation(invocation_id, "success")
        return response

    if track_invocation:
        finish_invocation(invocation_id, "error", f"Provider '{provider}' is not wired up yet")
    raise NotImplementedError(f"Provider '{provider}' is not wired up yet (model_id={model_id})")
