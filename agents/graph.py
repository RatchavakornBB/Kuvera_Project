"""The Analyst Lead subgraph — system-architecture.md Section 4.3 / Figure 4.
Deterministic sequencing via plain edges (the gate: 3.1 must finish before
3.2 starts) and Send() fan-out (3.3 and 3.4 both consume 3.2's completed
output, run in parallel) — never left to LLM judgment.

3.3 (IC memo drafter) and 3.4 (pricing advisor) are each a genuine
multi-step agentic loop (agents/loop_runner.py) — decide <-> act (the real
cyclic edge) -> finalize — instead of the single-shot node each used to be.
They still start from the same fan-out and still merge back to END exactly
as before; only what happens inside each branch changed. See
agents/state.py for why every loop's working fields are namespace-prefixed
(ic_memo_*, pricing_*) — the two branches run in parallel and must never
collide when LangGraph merges their partial state updates.

Checkpointer is Supabase Postgres from day one (AGENT.md Section 1) — never
swapped for an in-memory one, since that would change session-recovery
behavior and need re-architecting later.
"""

from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.types import Send

from agents.config import settings
from agents.nodes.doc_summarizer import doc_summarizer
from agents.nodes.ic_memo_drafter import ic_memo_act, ic_memo_decide, ic_memo_finalize, ic_memo_route
from agents.nodes.pricing_advisor import pricing_act, pricing_decide, pricing_finalize, pricing_route
from agents.nodes.risk_flagger import risk_flagger
from agents.state import AnalystState


def _fan_out(state: AnalystState) -> list[Send]:
    """3.2 risk_flagger has completed — the ic_memo and pricing loops both
    start from the same state, in parallel, per Figure 4."""
    return [Send("ic_memo_decide", state), Send("pricing_decide", state)]


def _build_graph() -> StateGraph:
    graph = StateGraph(AnalystState)
    graph.add_node("doc_summarizer", doc_summarizer)
    graph.add_node("risk_flagger", risk_flagger)
    graph.add_node("ic_memo_decide", ic_memo_decide)
    graph.add_node("ic_memo_act", ic_memo_act)
    graph.add_node("ic_memo_finalize", ic_memo_finalize)
    graph.add_node("pricing_decide", pricing_decide)
    graph.add_node("pricing_act", pricing_act)
    graph.add_node("pricing_finalize", pricing_finalize)

    graph.set_entry_point("doc_summarizer")
    graph.add_edge("doc_summarizer", "risk_flagger")  # the gate
    graph.add_conditional_edges("risk_flagger", _fan_out, ["ic_memo_decide", "pricing_decide"])

    graph.add_conditional_edges(
        "ic_memo_decide", ic_memo_route, {"act": "ic_memo_act", "finalize": "ic_memo_finalize", "truncated": "ic_memo_finalize"}
    )
    graph.add_edge("ic_memo_act", "ic_memo_decide")  # the cyclic edge
    graph.add_edge("ic_memo_finalize", END)

    graph.add_conditional_edges(
        "pricing_decide", pricing_route, {"act": "pricing_act", "finalize": "pricing_finalize", "truncated": "pricing_finalize"}
    )
    graph.add_edge("pricing_act", "pricing_decide")  # the cyclic edge
    graph.add_edge("pricing_finalize", END)
    return graph


@contextmanager
def compiled_analyst_graph():
    """Yields a compiled Analyst Lead graph backed by the Supabase Postgres
    Checkpointer. `setup()` is idempotent (CREATE TABLE IF NOT EXISTS-style)
    so calling it on every use is safe, not just a one-time migration step."""
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        checkpointer.setup()
        yield _build_graph().compile(checkpointer=checkpointer)
