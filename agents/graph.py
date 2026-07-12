"""The Analyst Lead subgraph — system-architecture.md Section 4.3 / Figure 4.
Deterministic sequencing via plain edges (the gate: 3.1 must finish before
3.2 starts) and Send() fan-out (3.3 and 3.4 both consume 3.2's completed
output, run in parallel) — never left to LLM judgment.

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
from agents.nodes.ic_memo_drafter import ic_memo_drafter
from agents.nodes.pricing_advisor import pricing_advisor
from agents.nodes.risk_flagger import risk_flagger
from agents.state import AnalystState


def _fan_out(state: AnalystState) -> list[Send]:
    """3.2 risk_flagger has completed — 3.3 and 3.4 both start from the
    same state, in parallel, per Figure 4."""
    return [Send("ic_memo_drafter", state), Send("pricing_advisor", state)]


def _build_graph() -> StateGraph:
    graph = StateGraph(AnalystState)
    graph.add_node("doc_summarizer", doc_summarizer)
    graph.add_node("risk_flagger", risk_flagger)
    graph.add_node("ic_memo_drafter", ic_memo_drafter)
    graph.add_node("pricing_advisor", pricing_advisor)

    graph.set_entry_point("doc_summarizer")
    graph.add_edge("doc_summarizer", "risk_flagger")  # the gate
    graph.add_conditional_edges("risk_flagger", _fan_out, ["ic_memo_drafter", "pricing_advisor"])
    graph.add_edge("ic_memo_drafter", END)
    graph.add_edge("pricing_advisor", END)
    return graph


@contextmanager
def compiled_analyst_graph():
    """Yields a compiled Analyst Lead graph backed by the Supabase Postgres
    Checkpointer. `setup()` is idempotent (CREATE TABLE IF NOT EXISTS-style)
    so calling it on every use is safe, not just a one-time migration step."""
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        checkpointer.setup()
        yield _build_graph().compile(checkpointer=checkpointer)
