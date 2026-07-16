"""Shared harness for a genuine multi-step agentic loop, expressed as LangGraph
cyclic edges rather than a hidden `while` loop inside one node. A loop-enabled
agent (Contracts Lead, IC memo drafter, pricing advisor) is three small nodes —
decide -> act -> decide (the cyclic edge) -> ... -> finalize — and every one of
those nodes calls into this module instead of reimplementing the tool-execution
mechanics per agent.

Every existing node in this codebase (risk_flagger, doc_summarizer, orchestrator,
etc.) makes exactly one call_model() call and returns — this module is for the
handful of agents that genuinely need to decide, act, observe, and decide again.
Do not reach for it for a single-shot classification/extraction node; that's
strictly a regression in cost and latency for no benefit.

Guardrails, all enforced here so no per-node reimplementation is possible to get
wrong: max_iterations (route_after_decide), a per-tool circuit breaker
(execute_tool_calls — a tool that fails circuit_breaker_threshold times in a row
is disabled for the rest of the run, never removed from the schema itself since
that would invalidate the prompt cache), and a run-scoped idempotency guard for
any future tool registered with idempotent=False (no tool in this codebase needs
it yet — search_knowledge is read-only — but the guard is real, not a stub, so a
future side-effecting tool can opt in without anyone rebuilding this)."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

import anthropic

from agents.adapters.model_adapter import call_model
from agents.invocation_steps import log_step

logger = logging.getLogger("agents")


@dataclass
class ToolSpec:
    """One tool available to a loop. `handler` is None only for the terminal
    (finish) tool — its input is read directly off the response by the node's
    `finalize` step, never dispatched through execute_tool_calls."""

    schema: dict
    handler: Callable[[dict], str] | None = None
    idempotent: bool = True
    terminal: bool = False


@dataclass
class ToolStep:
    index: int
    tool_name: str
    tool_input: dict
    tool_output: str | None
    status: str  # "success" | "error" | "skipped_circuit_broken" | "skipped_duplicate"


def _spec_by_name(tool_specs: list[ToolSpec]) -> dict[str, ToolSpec]:
    return {spec.schema["name"]: spec for spec in tool_specs}


def call_model_step(
    agent_name: str,
    messages: list[dict],
    tool_specs: list[ToolSpec],
    system: str | None = None,
    max_tokens: int = 8192,
) -> anthropic.types.Message:
    """One iteration's model call. The tool schema list is derived from
    tool_specs and passed unchanged on every call across a loop's iterations —
    never shrunk when a tool trips the circuit breaker — so the tools+system
    prefix stays byte-identical and prompt caching keeps working
    (shared/prompt-caching.md: a changed tool list invalidates the cache)."""
    tools = [spec.schema for spec in tool_specs]
    return call_model(
        agent_name,
        messages=messages,
        tools=tools,
        system=system,
        max_tokens=max_tokens,
        track_invocation=False,
    )


def _idempotency_key(tool_name: str, tool_input: dict) -> str:
    canonical = json.dumps(tool_input, sort_keys=True, default=str)
    return hashlib.sha256(f"{tool_name}:{canonical}".encode()).hexdigest()


def execute_tool_calls(
    response: anthropic.types.Message,
    tool_specs: list[ToolSpec],
    failure_counts: dict[str, int],
    tripped_tools: set[str],
    executed_side_effects: dict[str, str],
    circuit_breaker_threshold: int,
    invocation_id: str | None,
    step_offset: int = 0,
) -> tuple[list[dict], list[ToolStep], bool]:
    """Executes every non-terminal tool_use block in `response.content`. Returns
    (tool_result content blocks for a single user-turn message, the ToolStep log
    for this round, whether a terminal tool_use block was seen). Parallel tool
    calls are all handled and ALL their results returned together in one message
    — splitting them across messages silently trains the model to stop making
    parallel calls (shared/tool-use-concepts.md).

    Mutates failure_counts, tripped_tools, executed_side_effects in place —
    callers persist these in LangGraph state across the cyclic edge."""
    specs_by_name = _spec_by_name(tool_specs)
    tool_results: list[dict] = []
    steps: list[ToolStep] = []
    saw_terminal = False

    for i, block in enumerate(b for b in response.content if b.type == "tool_use"):
        spec = specs_by_name.get(block.name)
        if spec is None:
            # Model called something not in tool_specs — should not happen since
            # the API only offers tools we declared, but fail the single call
            # loud rather than silently dropping it and leaving the model
            # waiting forever for a tool_result it will never see.
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Unknown tool '{block.name}'.",
                    "is_error": True,
                }
            )
            continue

        if spec.terminal:
            saw_terminal = True
            # The terminal tool ends the loop; it is never "executed" here —
            # finalize() reads its input directly off `response`. No tool_result
            # is needed since the conversation ends at this turn.
            continue

        step_index = step_offset + len(steps)

        if block.name in tripped_tools:
            output = (
                f"Tool '{block.name}' failed {circuit_breaker_threshold} times in a row "
                "this run and has been disabled — do not call it again; proceed without "
                "it or finish with what you have."
            )
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": output, "is_error": True}
            )
            steps.append(ToolStep(step_index, block.name, block.input, output, "skipped_circuit_broken"))
            log_step(invocation_id, step_index, block.name, block.input, output, "skipped_circuit_broken")
            continue

        if not spec.idempotent:
            key = _idempotency_key(block.name, block.input)
            if key in executed_side_effects:
                output = executed_side_effects[key]
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
                steps.append(ToolStep(step_index, block.name, block.input, output, "skipped_duplicate"))
                log_step(invocation_id, step_index, block.name, block.input, output, "skipped_duplicate")
                continue

        try:
            output = spec.handler(block.input)  # type: ignore[misc]
            failure_counts[block.name] = 0
            if not spec.idempotent:
                executed_side_effects[_idempotency_key(block.name, block.input)] = output
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
            steps.append(ToolStep(step_index, block.name, block.input, output, "success"))
            log_step(invocation_id, step_index, block.name, block.input, output, "success")
        except Exception as e:  # noqa: BLE001 - a tool failure must degrade to a
            # tool_result the model can react to, never crash the loop.
            failure_counts[block.name] = failure_counts.get(block.name, 0) + 1
            if failure_counts[block.name] >= circuit_breaker_threshold:
                tripped_tools.add(block.name)
                logger.warning(
                    "loop_runner: tool '%s' tripped circuit breaker after %d failures",
                    block.name,
                    failure_counts[block.name],
                )
            error_text = str(e)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": error_text, "is_error": True}
            )
            steps.append(ToolStep(step_index, block.name, block.input, error_text, "error"))
            log_step(invocation_id, step_index, block.name, block.input, error_text, "error")

    return tool_results, steps, saw_terminal


def route_after_decide(
    response: anthropic.types.Message, iteration: int, max_iterations: int, tool_specs: list[ToolSpec]
) -> str:
    """Conditional-edge routing function for a loop's 'decide' node.

    'finalize' if the model is done (stop_reason != 'tool_use', or it called
    the terminal tool — checked against ToolSpec.terminal, not a naming
    convention, so any tool name works); 'truncated' if it still wants a
    non-terminal tool but the iteration cap is reached (the node's finalize
    step decides what truncation means — raise LoopTruncated, or degrade
    gracefully); else 'act'.
    """
    if response.stop_reason != "tool_use":
        return "finalize"
    specs_by_name = _spec_by_name(tool_specs)
    for block in response.content:
        if block.type != "tool_use":
            continue
        spec = specs_by_name.get(block.name)
        if spec is not None and spec.terminal:
            return "finalize"
    if iteration >= max_iterations:
        return "truncated"
    return "act"


def extract_terminal_input(response: anthropic.types.Message, terminal_tool_name: str) -> dict | None:
    """Pulls the terminal tool's structured input off the final response, for a
    'finalize' node to read. Returns None if the model didn't call it (the
    'truncated' route, or a malformed response) — callers must handle that."""
    for block in response.content:
        if block.type == "tool_use" and block.name == terminal_tool_name:
            return block.input
    return None
