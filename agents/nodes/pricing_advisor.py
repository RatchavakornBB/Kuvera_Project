"""3.4 Pricing advisor — system-architecture.md Section 7. Runs in
parallel with 3.3 ic_memo_drafter. Explicitly secondary, best-effort
(AGENT.md Section 10 / Section 11 invariant): its failure must never
block or degrade the response from doc_summarizer -> risk_flagger ->
ic_memo_drafter. On failure — including a truncated loop or a fully
circuit-broken search_knowledge — this node catches it itself and returns
pricing_note=None rather than raising — the one place in the whole
pipeline where a failure IS caught here rather than propagated, and
that's deliberate, not an oversight.

Was a single call_model() call with a forced, always-run
historical_precedent_context() pre-fetch; now a genuine multi-step
agentic loop (agents/loop_runner.py) split across decide/act/finalize
nodes connected by a real cyclic edge (agents/graph.py wires
pricing_act -> pricing_decide). The forced pre-fetch is gone — the model
now calls search_knowledge zero, one, or several times on demand instead
of always getting one fixed context block, whether or not it needed it."""

import logging
from dataclasses import asdict

from agents.activity_tracker import finish_invocation, start_invocation
from agents.errors import LoopTruncated, NodeFailure
from agents.loop_runner import ToolSpec, call_model_step, execute_tool_calls, extract_terminal_input, route_after_decide
from agents.state import AnalystState
from agents.tools.knowledge_tool import SEARCH_KNOWLEDGE_SPEC

logger = logging.getLogger("agents")

REPORT_PRICING_TOOL = {
    "name": "report_pricing_note",
    "description": "Report the final pricing note. Call this once you are done.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pricing_note": {
                "type": ["string", "null"],
                "description": "One short paragraph of indicative pricing/commercial terms, or null if the data is insufficient.",
            },
            "insufficient_data": {
                "type": "boolean",
                "description": "true if the summary lacks enough real financial data to ground a suggestion — set pricing_note to null in that case.",
            },
        },
        "required": ["insufficient_data"],
    },
}

PRICING_TOOLS = [
    SEARCH_KNOWLEDGE_SPEC,
    ToolSpec(schema=REPORT_PRICING_TOOL, handler=None, terminal=True),
]

PRICING_MAX_ITERATIONS = 3
PRICING_CIRCUIT_BREAKER_THRESHOLD = 2

INSTRUCTIONS = """You are the Analyst Lead's pricing advisor for an M&A due diligence review.
Based on the summary and risk flags below, suggest indicative pricing or commercial terms
ONLY if the summary contains enough real financial data (e.g. revenue, margin, growth) to
ground a suggestion. If the data is insufficient, say so plainly instead of guessing — do
not invent a number. Keep it to one short paragraph.

If comparable-deal pricing precedent would help ground your suggestion, call
search_knowledge — do not call it speculatively, and do not call it more than once or twice.
When you are done, call report_pricing_note with the result.

SUMMARY:
{summary}

RISK FLAGS:
{risk_flags}
"""


def _format_risk_flags(risk_flags: list[dict]) -> str:
    if not risk_flags:
        return "(none identified)"
    return "\n".join(f"- [{r['severity']}] {r['description']}" for r in risk_flags)


def pricing_decide(state: AnalystState) -> dict:
    if "pricing_messages" not in state:
        prompt = INSTRUCTIONS.format(summary=state["summary"], risk_flags=_format_risk_flags(state.get("risk_flags", [])))
        messages = [{"role": "user", "content": prompt}]
        iteration = 0
        step_count = 0
        steps: list[dict] = []
        tool_failure_counts: dict[str, int] = {}
        tripped_tools: list[str] = []
        executed_side_effects: dict[str, str] = {}
        invocation_id = start_invocation("pricing_advisor")
    else:
        messages = state["pricing_messages"]
        iteration = state["pricing_iteration"]
        step_count = state["pricing_step_count"]
        steps = state["pricing_steps"]
        tool_failure_counts = state["pricing_tool_failures"]
        tripped_tools = state["pricing_tripped_tools"]
        executed_side_effects = state["pricing_executed_side_effects"]
        invocation_id = state["pricing_invocation_id"]

    try:
        response = call_model_step("pricing_advisor", messages, PRICING_TOOLS, system=None, max_tokens=1536)
    except Exception as e:
        # A model-call failure mid-loop degrades exactly like a truncated
        # loop does — see pricing_finalize's except clause below. Recorded
        # here as a completed (failed) invocation immediately since there's
        # no further node call to reach finalize's own bookkeeping.
        finish_invocation(invocation_id, "error", str(e))
        raise NodeFailure(node="pricing_advisor", attempts=iteration + 1, reason="model call failed", raw_error=str(e))

    messages = messages + [{"role": "assistant", "content": response.content}]

    return {
        "pricing_messages": messages,
        "pricing_last_response": response,
        "pricing_iteration": iteration + 1,
        "pricing_step_count": step_count,
        "pricing_steps": steps,
        "pricing_tool_failures": tool_failure_counts,
        "pricing_tripped_tools": tripped_tools,
        "pricing_executed_side_effects": executed_side_effects,
        "pricing_invocation_id": invocation_id,
    }


def pricing_act(state: AnalystState) -> dict:
    failure_counts = dict(state["pricing_tool_failures"])
    tripped = set(state["pricing_tripped_tools"])
    side_effects = dict(state["pricing_executed_side_effects"])

    tool_results, steps, _ = execute_tool_calls(
        state["pricing_last_response"],
        PRICING_TOOLS,
        failure_counts,
        tripped,
        side_effects,
        PRICING_CIRCUIT_BREAKER_THRESHOLD,
        state["pricing_invocation_id"],
        step_offset=state["pricing_step_count"],
    )

    messages = state["pricing_messages"] + [{"role": "user", "content": tool_results}]
    return {
        "pricing_messages": messages,
        "pricing_step_count": state["pricing_step_count"] + len(steps),
        "pricing_steps": state["pricing_steps"] + [asdict(s) for s in steps],
        "pricing_tool_failures": failure_counts,
        "pricing_tripped_tools": list(tripped),
        "pricing_executed_side_effects": side_effects,
    }


def pricing_finalize(state: AnalystState) -> dict:
    result = extract_terminal_input(state["pricing_last_response"], "report_pricing_note")

    if result is None:
        error = LoopTruncated(
            node="pricing_advisor", max_iterations=PRICING_MAX_ITERATIONS, steps=state.get("pricing_steps", [])
        )
        finish_invocation(state["pricing_invocation_id"], "error", error.reason)
        logger.warning("pricing_advisor degraded gracefully: %s", error)
        return {"pricing_note": None, "pricing_error": error.to_dict()}

    finish_invocation(state["pricing_invocation_id"], "success")
    pricing_note = None if result.get("insufficient_data") else result.get("pricing_note")
    return {"pricing_note": pricing_note}


def pricing_route(state: AnalystState) -> str:
    return route_after_decide(state["pricing_last_response"], state["pricing_iteration"], PRICING_MAX_ITERATIONS, PRICING_TOOLS)
