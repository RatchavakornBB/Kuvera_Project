"""Web research — system-architecture.md Section 5.2/5.3. Combines
Claude's official web_search server tool (not a custom scraper; citations
parsed from the real citations array) with a hard-routed SEC EDGAR lookup.

EDGAR routing is a plain Python conditional, not an LLM decision (Section
5.3: "implemented as a plain conditional in the Analyst Lead's
tool-selection step, not a call through the Orchestrator's LLM router") —
keyword-triggered here, deliberately simple rather than another
LLM classification call for what's meant to be a deterministic hard-route.
"""

import re

from agents.adapters.model_adapter import call_model
from agents.retry import with_retry
from agents.tools.sec_edgar import fetch_company_filings

EDGAR_TRIGGER_RE = re.compile(
    r"\b(10-K|10-Q|20-F|SEC filing|annual report|quarterly report|EDGAR)\b", re.IGNORECASE
)

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 3}

RESEARCH_PROMPT = (
    "You are the Analyst Lead's research assistant. Answer the question below using web "
    "search for current, real-world information. Cite what you find. Keep the answer "
    "concise (a few sentences to a short paragraph).\n\nQUESTION: {question}{edgar_context}"
)


# Sentence-starting imperative/question words that are capitalized but are
# never a company name — found via a real test where "Look up Medtronic's
# 10-K" extracted "Look" as the first candidate, which then substring-
# matched "Outlook Therapeutics" (word-boundary fix in sec_edgar.py caught
# most of this, but filtering obviously-wrong candidates here too avoids
# wasting an EDGAR round trip on them in the first place).
_NON_COMPANY_WORDS = {
    "look", "please", "show", "what", "find", "get", "tell", "give", "pull",
    "fetch", "check", "search", "can", "could", "would", "the", "sec", "edgar",
}


def _maybe_edgar_context(question: str) -> tuple[str, dict | None]:
    if not EDGAR_TRIGGER_RE.search(question):
        return "", None

    # Hard-routed: try to pull a company name out of the question with a
    # light heuristic (capitalized word sequence) rather than an LLM call —
    # good enough for the explicit "look up <Company>'s 10-K" phrasing this
    # routes on.
    candidates = re.findall(r"\b([A-Z][A-Za-z&.]*(?:\s+[A-Z][A-Za-z&.]*){0,3})\b", question)
    candidates = [c for c in candidates if c.lower() not in _NON_COMPANY_WORDS]
    for candidate in candidates:
        result = fetch_company_filings(candidate)
        if result:
            filing_lines = "\n".join(
                f"  - {f['form']} filed {f['filing_date']} (accession {f['accession_number']})"
                for f in result["filings"]
            )
            context = (
                f"\n\nSEC EDGAR filings for {result['company']} ({result['ticker']}):\n{filing_lines}"
            )
            return context, result
    return "", None


def _run_once(question: str) -> dict:
    edgar_context, edgar_result = _maybe_edgar_context(question)

    response = call_model(
        "orchestrator",
        messages=[{"role": "user", "content": RESEARCH_PROMPT.format(question=question, edgar_context=edgar_context)}],
        tools=[WEB_SEARCH_TOOL],
        max_tokens=1536,
    )

    answer_parts = []
    citations = []
    for block in response.content:
        if block.type == "text":
            answer_parts.append(block.text)
            for citation in getattr(block, "citations", None) or []:
                citations.append(
                    {
                        "url": getattr(citation, "url", None),
                        "title": getattr(citation, "title", None),
                        "cited_text": getattr(citation, "cited_text", None),
                    }
                )

    if not answer_parts:
        raise ValueError(f"model returned no text block (stop_reason={response.stop_reason!r})")

    return {"answer": "".join(answer_parts), "citations": citations, "edgar": edgar_result}


def web_research(question: str) -> dict:
    return with_retry("web_research", lambda: _run_once(question))
