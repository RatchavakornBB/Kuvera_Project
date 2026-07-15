"""Chat-driven Drafting Lead sub-routing — mirrors
agents/nodes/stage_update.py's two-stage pattern: the Orchestrator only
does coarse routing to 'drafting_lead', this node resolves WHICH of the
four artifacts (memo, deck, cover email, source-cited summary) the user
actually asked for. Keeps fine-grained interpretation inside the Lead
rather than bloating the Orchestrator's single classification call with
every Lead's own sub-decisions."""

from agents.adapters.model_adapter import call_model
from agents.retry import with_retry

DRAFT_TYPES = ("memo", "deck", "email", "summary")

DRAFT_TYPE_TOOL = {
    "name": "select_draft_type",
    "description": "Decide which Drafting Lead artifact the user is asking for.",
    "input_schema": {
        "type": "object",
        "properties": {
            "draft_type": {
                "type": "string",
                "enum": list(DRAFT_TYPES),
                "description": (
                    "'memo' for an IC memo (.docx), 'deck' for an IC deck/presentation "
                    "(.pptx), 'email' for a cover email draft, 'summary' for a "
                    "source-cited summary."
                ),
            }
        },
        "required": ["draft_type"],
    },
}

SYSTEM_PROMPT = (
    "The user is asking the Drafting Lead to produce one specific artifact for this "
    "deal. Call select_draft_type with which one they mean."
)


def _run_once(message: str) -> str:
    response = call_model(
        "drafting_router",
        messages=[{"role": "user", "content": f"{SYSTEM_PROMPT}\n\nMESSAGE: {message}"}],
        tools=[DRAFT_TYPE_TOOL],
        max_tokens=256,
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "select_draft_type":
            draft_type = block.input.get("draft_type")
            if draft_type not in DRAFT_TYPES:
                raise ValueError(f"tool_use returned an invalid draft_type: {draft_type!r}")
            return draft_type
    raise ValueError(f"model did not call select_draft_type (stop_reason={response.stop_reason!r})")


def classify_draft_type(message: str) -> str:
    return with_retry("drafting_router", lambda: _run_once(message))
