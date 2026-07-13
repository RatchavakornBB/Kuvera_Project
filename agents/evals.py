"""A minimal, real eval framework — none existed anywhere in this codebase before this
(ux-ui-spec.md Section 3.6's "Eval pass-rate bar" was previously the one piece of the Admin spec
left entirely unbuilt). Real LLM-as-judge grading against a small, real test set per agent, run
on-demand against a *candidate* skill_content (so an admin can sanity-check a proposed change
before approving it, not only after).

Scope, stated honestly: this tests an agent's core prompt+skill behavior via a direct model call
with a synthetic input, not the full node pipeline (several real nodes need an actual uploaded
document or deal_id, which an eval harness can't fabricate without lying about what it's testing).
Eval cases exist for 3 agents with clear, checkable behavior; agents without cases defined return
`pass_rate: None`, not a fabricated score."""

from functools import lru_cache
from typing import Any

import anthropic

from agents.config import settings

DEFAULT_MODEL = "claude-sonnet-5"

RISK_FLAGGER_TOOL = {
    "name": "report_risk_flags",
    "description": "Report the structured list of risk flags identified for this deal.",
    "input_schema": {
        "type": "object",
        "properties": {
            "risk_flags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["high", "medium"]},
                        "description": {"type": "string"},
                        "source_excerpt": {"type": "string"},
                    },
                    "required": ["severity", "description", "source_excerpt"],
                },
            }
        },
        "required": ["risk_flags"],
    },
}

EVAL_CASES: dict[str, list[dict[str, Any]]] = {
    "pricing_advisor": [
        {
            "prompt": (
                "You are the Analyst Lead's pricing advisor for an M&A due diligence review. "
                "Based on the summary below, suggest indicative pricing ONLY if there is enough "
                "real financial data to ground it. If insufficient, say so plainly instead of "
                "guessing.\n\nSUMMARY:\nTarget company reported FY2025 revenue of 120M THB, "
                "EBITDA margin of 22%, and 15% YoY growth. Comparable transactions in this sector "
                "have traded at 8-10x EBITDA."
            ),
            "criteria": "Should produce an actual indicative pricing figure or range grounded in the given revenue/EBITDA/multiple data, not decline to price.",
        },
        {
            "prompt": (
                "You are the Analyst Lead's pricing advisor for an M&A due diligence review. "
                "Based on the summary below, suggest indicative pricing ONLY if there is enough "
                "real financial data to ground it. If insufficient, say so plainly instead of "
                "guessing.\n\nSUMMARY:\nTarget company's services agreement was reviewed. No "
                "revenue, EBITDA, or valuation figures were present in the document."
            ),
            "criteria": "Should explicitly decline to give a pricing figure due to insufficient data, NOT invent a number.",
        },
    ],
    "ic_memo_drafter": [
        {
            "prompt": (
                "You are the Analyst Lead's IC memo drafter. Draft a concise IC memo in markdown "
                "from the summary and risk flags below.\n\nSUMMARY:\nTarget is a healthcare "
                "logistics company with a change-of-control clause requiring counterparty "
                "consent.\n\nRISK FLAGS:\n- [high] Change-of-control clause allows counterparty "
                "to terminate without consent."
            ),
            "criteria": "The drafted memo should explicitly mention the change-of-control risk from the input, not omit it.",
        },
    ],
    "risk_flagger": [
        {
            "prompt": (
                "You are the Analyst Lead's risk flagger. Given the summary below, identify "
                "missing information and key investment risks. Call report_risk_flags.\n\n"
                "NEW SUMMARY:\nThis MSA between two Thailand-based healthcare entities involves "
                "processing of sensitive patient data. The agreement contains no data-privacy, "
                "PDPA compliance, or breach-notification provisions of any kind."
            ),
            "criteria": "Should flag the complete absence of PDPA/data-privacy provisions as a risk (any severity).",
            "tools": [RISK_FLAGGER_TOOL],
        },
    ],
}

JUDGE_PROMPT = """You are grading an AI agent's output for an M&A due-diligence platform's eval
suite. Be strict but fair.

CRITERIA: {criteria}

AGENT OUTPUT:
{output}

Does the output satisfy the criteria? Respond with exactly PASS or FAIL on the first line, then a
one-sentence reason on the second line."""


@lru_cache
def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _run_candidate(prompt: str, system: str, model_id: str, tools: list[dict] | None) -> str:
    kwargs: dict[str, Any] = {"model": model_id, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools
    response = _client().messages.create(**kwargs)

    for block in response.content:
        if block.type == "tool_use":
            import json

            return json.dumps(block.input)
    for block in response.content:
        if block.type == "text":
            return block.text
    return "(no output)"


def _grade(criteria: str, output: str) -> tuple[bool, str]:
    response = _client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(criteria=criteria, output=output)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    first_line = text.split("\n")[0].upper()
    return first_line.startswith("PASS"), text


def run_eval(agent_name: str, skill_content: str, model_id: str = DEFAULT_MODEL) -> dict[str, Any]:
    cases = EVAL_CASES.get(agent_name)
    if not cases:
        return {"pass_rate": None, "results": [], "note": "No eval cases defined for this agent"}

    results = []
    for case in cases:
        output = _run_candidate(case["prompt"], skill_content, model_id, case.get("tools"))
        passed, reason = _grade(case["criteria"], output)
        results.append(
            {
                "criteria": case["criteria"],
                "output": output[:500],
                "passed": passed,
                "reason": reason,
            }
        )

    pass_rate = sum(1 for r in results if r["passed"]) / len(results)
    return {"pass_rate": pass_rate, "results": results}
