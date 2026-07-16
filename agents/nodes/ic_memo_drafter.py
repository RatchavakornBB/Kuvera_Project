"""3.3 IC memo drafter — system-architecture.md Section 7. Runs in parallel
with 3.4 pricing_advisor once the gate (3.1 -> 3.2) completes; both consume
the same summary + risk_flags. This is a core deliverable alongside
risk_flagger (AGENT.md Section 10) — its failure is never swallowed.

Was a single call_model() call; now a genuine multi-step agentic loop
(agents/loop_runner.py) split across three LangGraph nodes — decide, act,
finalize — connected by a real cyclic edge (agents/graph.py wires
ic_memo_act -> ic_memo_decide). The model can call search_knowledge for
comparable-deal precedent before finishing, rather than being grounded only
in the summary/risk_flags handed to it. No new guardrail code here — every
node just calls into the shared harness."""

from dataclasses import asdict

from agents.activity_tracker import finish_invocation, start_invocation
from agents.errors import LoopTruncated
from agents.loop_runner import ToolSpec, call_model_step, execute_tool_calls, extract_terminal_input, route_after_decide
from agents.state import AnalystState
from agents.tools.knowledge_tool import SEARCH_KNOWLEDGE_SPEC

REPORT_IC_MEMO_TOOL = {
    "name": "report_ic_memo",
    "description": "Report the final IC memo in markdown. Call this once you are done.",
    "input_schema": {
        "type": "object",
        "properties": {"memo_markdown": {"type": "string"}},
        "required": ["memo_markdown"],
    },
}

IC_MEMO_TOOLS = [
    SEARCH_KNOWLEDGE_SPEC,
    ToolSpec(schema=REPORT_IC_MEMO_TOOL, handler=None, terminal=True),
]

IC_MEMO_MAX_ITERATIONS = 3
IC_MEMO_CIRCUIT_BREAKER_THRESHOLD = 2

INSTRUCTIONS = """You are the Analyst Lead's IC memo drafter for an M&A due diligence review.
Draft a concise internal investment committee memo in markdown from the summary and risk
flags below. Structure: a short deal overview paragraph, a "Key Financials" section, a
"Risks" section (group by severity), and a one-paragraph recommendation on next steps.
Ground every claim in the summary/risk flags given — do not invent figures.

If comparable-deal precedent (similar pricing, similar risk outcomes) would materially
strengthen the recommendation, call search_knowledge first — do not call it speculatively,
and do not call it more than once or twice. When you are done, call report_ic_memo with the
final memo.

SUMMARY:
{summary}

RISK FLAGS:
{risk_flags}
"""


def _format_risk_flags(risk_flags: list[dict]) -> str:
    if not risk_flags:
        return "(none identified)"
    return "\n".join(f"- [{r['severity']}] {r['description']}" for r in risk_flags)


def ic_memo_decide(state: AnalystState) -> dict:
    if "ic_memo_messages" not in state:
        prompt = INSTRUCTIONS.format(summary=state["summary"], risk_flags=_format_risk_flags(state.get("risk_flags", [])))
        messages = [{"role": "user", "content": prompt}]
        iteration = 0
        step_count = 0
        steps: list[dict] = []
        tool_failure_counts: dict[str, int] = {}
        tripped_tools: list[str] = []
        executed_side_effects: dict[str, str] = {}
        invocation_id = start_invocation("ic_memo_drafter")
    else:
        messages = state["ic_memo_messages"]
        iteration = state["ic_memo_iteration"]
        step_count = state["ic_memo_step_count"]
        steps = state["ic_memo_steps"]
        tool_failure_counts = state["ic_memo_tool_failures"]
        tripped_tools = state["ic_memo_tripped_tools"]
        executed_side_effects = state["ic_memo_executed_side_effects"]
        invocation_id = state["ic_memo_invocation_id"]

    response = call_model_step("ic_memo_drafter", messages, IC_MEMO_TOOLS, system=None, max_tokens=4096)
    messages = messages + [{"role": "assistant", "content": response.content}]

    return {
        "ic_memo_messages": messages,
        "ic_memo_last_response": response,
        "ic_memo_iteration": iteration + 1,
        "ic_memo_step_count": step_count,
        "ic_memo_steps": steps,
        "ic_memo_tool_failures": tool_failure_counts,
        "ic_memo_tripped_tools": tripped_tools,
        "ic_memo_executed_side_effects": executed_side_effects,
        "ic_memo_invocation_id": invocation_id,
    }


def ic_memo_act(state: AnalystState) -> dict:
    failure_counts = dict(state["ic_memo_tool_failures"])
    tripped = set(state["ic_memo_tripped_tools"])
    side_effects = dict(state["ic_memo_executed_side_effects"])

    tool_results, steps, _ = execute_tool_calls(
        state["ic_memo_last_response"],
        IC_MEMO_TOOLS,
        failure_counts,
        tripped,
        side_effects,
        IC_MEMO_CIRCUIT_BREAKER_THRESHOLD,
        state["ic_memo_invocation_id"],
        step_offset=state["ic_memo_step_count"],
    )

    messages = state["ic_memo_messages"] + [{"role": "user", "content": tool_results}]
    return {
        "ic_memo_messages": messages,
        "ic_memo_step_count": state["ic_memo_step_count"] + len(steps),
        "ic_memo_steps": state["ic_memo_steps"] + [asdict(s) for s in steps],
        "ic_memo_tool_failures": failure_counts,
        "ic_memo_tripped_tools": list(tripped),
        "ic_memo_executed_side_effects": side_effects,
    }


def ic_memo_finalize(state: AnalystState) -> dict:
    result = extract_terminal_input(state["ic_memo_last_response"], "report_ic_memo")

    if result is None:
        finish_invocation(state["ic_memo_invocation_id"], "error", "loop truncated without calling report_ic_memo")
        # LoopTruncated IS a NodeFailure (agents/errors.py) — this propagates
        # out of graph.invoke() exactly like today's risk_flagger NodeFailure
        # does, caught by the same route-level `except NodeFailure` handlers
        # (backend/app/routes/analyze.py) without any of those needing a
        # second except clause. ic_memo_drafter's contract (never swallowed)
        # means truncation fails loud here, not a silent/degraded output.
        raise LoopTruncated(
            node="ic_memo_drafter", max_iterations=IC_MEMO_MAX_ITERATIONS, steps=state.get("ic_memo_steps", [])
        )

    finish_invocation(state["ic_memo_invocation_id"], "success")
    return {"ic_memo_draft": result.get("memo_markdown", "")}


def ic_memo_route(state: AnalystState) -> str:
    return route_after_decide(state["ic_memo_last_response"], state["ic_memo_iteration"], IC_MEMO_MAX_ITERATIONS, IC_MEMO_TOOLS)
