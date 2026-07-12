from typing import TypedDict


class RiskFlag(TypedDict):
    severity: str
    description: str
    source_excerpt: str


class AnalystState(TypedDict, total=False):
    deal_id: str
    document_id: str
    summary: str
    risk_flags: list[RiskFlag]
    ic_memo_draft: str
    pricing_note: str | None
    pricing_error: dict  # set only if pricing_advisor degraded gracefully (AGENT.md Section 10)
