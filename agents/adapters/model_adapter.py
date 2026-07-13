"""The only path to any LLM provider — every LangGraph node calls
call_model(), never a provider SDK directly (AGENT.md Section 1 / 11).

Only Claude is actually called this week, but the shape here is what makes
adding a second provider a config change instead of a node rewrite later:
look up agent_name's model_id, dispatch to the client for that model_id's
provider.
"""

from functools import lru_cache

import anthropic

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
    "concierge_qa": "claude-sonnet-5",
    "orchestrator": "claude-sonnet-5",
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


@lru_cache
def _anthropic_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def call_model(
    agent_name: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    system: str | None = None,
    max_tokens: int = 4096,
) -> anthropic.types.Message:
    """Dispatches a chat completion for `agent_name` to that agent's
    configured model_id. Returns the provider's native response object —
    single-provider for now, so no normalization layer exists yet
    (add one only once a second provider is actually wired in)."""

    model_id = AGENT_MODELS.get(agent_name, DEFAULT_MODEL)
    provider = _provider_for(model_id)

    if provider == "anthropic":
        client = _anthropic_client()
        kwargs: dict = {"model": model_id, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        return client.messages.create(**kwargs)

    raise NotImplementedError(f"Provider '{provider}' is not wired up yet (model_id={model_id})")
