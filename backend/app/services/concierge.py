from typing import Any

from agents.nodes.concierge_qa import concierge_qa


def ask_about_deal(deal_id: str, question: str) -> dict[str, Any]:
    return concierge_qa(deal_id=deal_id, question=question)
