"""Chat-driven stage change — the third of the three ways a deal's stage
can move (manual UI control, this, and the scheduler's stalled-status
flag). Only extracts *intent* (which stage, and a confirmation sentence);
the actual write goes through app.services.deals.update_deal_stage, same
as the UI path, so there is exactly one place that touches the `stage`
column."""

from agents.adapters.model_adapter import call_model
from agents.deal_context import build_deal_context
from agents.retry import with_retry

STAGES = (
    "Lead",
    "NDA",
    "Sourcing & Screening",
    "Valuation & Bidding",
    "Strategy & Preparation",
    "Due Diligence",
    "Negotiation & Closing",
)

STAGE_UPDATE_TOOL = {
    "name": "update_stage",
    "description": "Move this deal to a new stage in the pipeline, based on what the user asked for.",
    "input_schema": {
        "type": "object",
        "properties": {
            "stage": {
                "type": "string",
                "enum": list(STAGES),
                "description": "The target stage, resolved from the user's message (e.g. 'move to the next stage' means the stage immediately after the current one).",
            },
            "confirmation": {
                "type": "string",
                "description": "One sentence to show the user confirming what changed, e.g. 'Moved Deal A from NDA to Sourcing & Screening.'",
            },
        },
        "required": ["stage", "confirmation"],
    },
}

SYSTEM_PROMPT = (
    "You are Concierge, the Kuvera Assistant. The user wants to change this deal's pipeline "
    f"stage. Valid stages, in order, are: {', '.join(STAGES)}. Resolve their request to exactly "
    "one target stage using the deal data below (e.g. 'advance to the next stage' means the one "
    "after the current stage; an explicit stage name means that stage). Call update_stage with "
    "your result."
)


def _run_once(deal_id: str, message: str) -> dict:
    context = build_deal_context(deal_id)

    response = call_model(
        "stage_update",
        messages=[
            {
                "role": "user",
                "content": f"{SYSTEM_PROMPT}\n\nDEAL DATA:\n{context}\n\nREQUEST: {message}",
            }
        ],
        tools=[STAGE_UPDATE_TOOL],
        max_tokens=512,
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "update_stage":
            stage = block.input.get("stage")
            if stage not in STAGES:
                raise ValueError(f"tool_use returned an invalid stage: {stage!r}")
            return {"stage": stage, "confirmation": block.input.get("confirmation", f"Moved to {stage}.")}

    raise ValueError(f"model did not call update_stage (stop_reason={response.stop_reason!r})")


def extract_stage_update(deal_id: str, message: str) -> dict:
    return with_retry("stage_update", lambda: _run_once(deal_id, message))
