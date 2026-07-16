"""Contracts Lead — a genuine multi-step agentic loop, replacing the old
ingest-triggered pair of single-shot functions (contract_summarizer,
clause_extractor) with one LangGraph subgraph that can decide, on its own,
whether comparable-deal precedent (search_knowledge) is worth pulling in
before reporting its final summary and clauses.

Structure: init -> decide <-> act -> finalize, mirroring agents/graph.py's
compiled_analyst_graph() pattern (same Postgres checkpointer, same
context-manager shape). The decide <-> act edge is the real cyclic edge —
see agents/loop_runner.py for the shared tool-execution mechanics
(max_iterations, per-tool circuit breaker, idempotency guard) every
loop-enabled agent in this codebase reuses rather than reimplementing."""

import json
from contextlib import contextmanager
from dataclasses import asdict

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph

from agents.activity_tracker import finish_invocation, start_invocation
from agents.config import settings
from agents.contracts_state import ContractsState
from agents.documents import build_content_block, fetch_document, get_document_deal_id
from agents.errors import LoopTruncated
from agents.loop_runner import ToolSpec, call_model_step, execute_tool_calls, extract_terminal_input, route_after_decide
from agents.tools.knowledge_tool import SEARCH_KNOWLEDGE_SPEC

REPORT_CONTRACT_ANALYSIS_TOOL = {
    "name": "report_contract_analysis",
    "description": "Report the final contract summary and extracted clauses. Call this once you are done.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "A few tight paragraphs: parties, core commercial terms, term/renewal structure, anything unusual.",
            },
            "clauses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "Short clause type, e.g. 'Change of control'"},
                        "text": {"type": "string", "description": "The clause itself, quoted or tightly paraphrased"},
                    },
                    "required": ["label", "text"],
                },
            },
        },
        "required": ["summary", "clauses"],
    },
}

CONTRACTS_TOOLS = [
    SEARCH_KNOWLEDGE_SPEC,
    ToolSpec(schema=REPORT_CONTRACT_ANALYSIS_TOOL, handler=None, terminal=True),
]

MAX_ITERATIONS = 5
CIRCUIT_BREAKER_THRESHOLD = 2

INSTRUCTIONS = (
    "You are the Contracts Lead. Summarize this contract for an analyst — the parties, "
    "the core commercial terms, the term/renewal structure, and anything unusual "
    "(change-of-control provisions, exclusivity, non-standard liability terms) — and "
    "extract its key clauses (term/renewal, termination, change-of-control, "
    "liability/indemnification, exclusivity, and any other clause a due-diligence "
    "analyst would need to know about).\n\n"
    "If comparable-deal precedent would help you judge whether a term is standard or "
    "unusual, call search_knowledge first — do not call it speculatively, and do not "
    "call it more than once or twice. When you are done, call report_contract_analysis "
    "with the final summary and clauses."
)


def _normalize_clauses(value: object) -> list[dict]:
    # Same defensive parsing agents/nodes/clause_extractor.py already needed —
    # Claude's tool_use output for an array-typed field is usually
    # schema-conformant but has been observed returning a JSON-encoded string
    # (itself wrapping a redundant {"clauses": [...]} dict) instead of the raw
    # array.
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    if isinstance(value, dict) and "clauses" in value:
        value = value["clauses"]
    return value if isinstance(value, list) else []


def _init(state: ContractsState) -> ContractsState:
    content, _filename, media_type = fetch_document(state["document_id"])
    deal_id = get_document_deal_id(state["document_id"])
    invocation_id = start_invocation("contracts_lead")

    messages = [
        {
            "role": "user",
            "content": [
                build_content_block(content, media_type),
                {"type": "text", "text": INSTRUCTIONS},
            ],
        }
    ]

    return {
        **state,
        "deal_id": deal_id,
        "messages": messages,
        "iteration": 0,
        "step_count": 0,
        "steps": [],
        "tool_failure_counts": {},
        "tripped_tools": [],
        "executed_side_effects": {},
        "invocation_id": invocation_id,
    }


def _decide(state: ContractsState) -> ContractsState:
    response = call_model_step("contracts_lead", state["messages"], CONTRACTS_TOOLS, system=None, max_tokens=8192)
    messages = state["messages"] + [{"role": "assistant", "content": response.content}]
    return {**state, "messages": messages, "last_response": response, "iteration": state["iteration"] + 1}


def _act(state: ContractsState) -> ContractsState:
    failure_counts = dict(state["tool_failure_counts"])
    tripped = set(state["tripped_tools"])
    side_effects = dict(state["executed_side_effects"])

    tool_results, steps, _ = execute_tool_calls(
        state["last_response"],
        CONTRACTS_TOOLS,
        failure_counts,
        tripped,
        side_effects,
        CIRCUIT_BREAKER_THRESHOLD,
        state["invocation_id"],
        step_offset=state["step_count"],
    )

    messages = state["messages"] + [{"role": "user", "content": tool_results}]
    return {
        **state,
        "messages": messages,
        "step_count": state["step_count"] + len(steps),
        "steps": state["steps"] + [asdict(s) for s in steps],
        "tool_failure_counts": failure_counts,
        "tripped_tools": list(tripped),
        "executed_side_effects": side_effects,
    }


def _finalize(state: ContractsState) -> ContractsState:
    result = extract_terminal_input(state["last_response"], "report_contract_analysis")

    if result is None:
        finish_invocation(state["invocation_id"], "error", "loop truncated without calling report_contract_analysis")
        raise LoopTruncated(node="contracts_lead", max_iterations=MAX_ITERATIONS, steps=state.get("steps", []))

    finish_invocation(state["invocation_id"], "success")
    return {
        **state,
        "summary": result.get("summary", ""),
        "clauses": _normalize_clauses(result.get("clauses")),
        "circuit_broken_tools": state["tripped_tools"],
    }


def _route(state: ContractsState) -> str:
    return route_after_decide(state["last_response"], state["iteration"], MAX_ITERATIONS, CONTRACTS_TOOLS)


def _build_graph() -> StateGraph:
    graph = StateGraph(ContractsState)
    graph.add_node("init", _init)
    graph.add_node("decide", _decide)
    graph.add_node("act", _act)
    graph.add_node("finalize", _finalize)

    graph.set_entry_point("init")
    graph.add_edge("init", "decide")
    graph.add_conditional_edges("decide", _route, {"act": "act", "finalize": "finalize", "truncated": "finalize"})
    graph.add_edge("act", "decide")  # the cyclic edge
    graph.add_edge("finalize", END)
    return graph


@contextmanager
def compiled_contracts_graph():
    """Yields a compiled Contracts Lead graph backed by the same Supabase
    Postgres Checkpointer every other graph in this codebase uses. `setup()`
    is idempotent, safe to call on every use (agents/graph.py's same
    convention)."""
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        checkpointer.setup()
        yield _build_graph().compile(checkpointer=checkpointer)
