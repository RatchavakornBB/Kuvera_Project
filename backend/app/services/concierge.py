from typing import Any, Callable

from agents.nodes.concierge_qa import concierge_qa


def ask_about_deal(
    deal_id: str, question: str, on_delta: Callable[[str], None] | None = None
) -> dict[str, Any]:
    return concierge_qa(deal_id=deal_id, question=question, on_delta=on_delta)
