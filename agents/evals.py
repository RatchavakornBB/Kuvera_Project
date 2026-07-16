"""A real eval framework — none existed anywhere in this codebase before this
(ux-ui-spec.md Section 3.6's "Eval pass-rate bar" was previously the one piece of the Admin spec
left entirely unbuilt). Real LLM-as-judge grading against a small, real test set per agent, run
on-demand against a *candidate* skill_content (so an admin can sanity-check a proposed change
before approving it, not only after).

Scope, stated honestly: this tests an agent's core prompt+skill behavior via a direct model call
with a synthetic input, not the full node pipeline (several real nodes need an actual uploaded
document or deal_id, which an eval harness can't fabricate without lying about what it's testing).

Two sources of eval cases, merged per agent_name in run_eval():
  - EVAL_CASES below: built-in, code-reviewed fixtures, one entry per agent currently wired up in
    AGENT_MODELS (agents/adapters/model_adapter.py) — all 13 have at least one case now.
  - agents/eval_cases.py: admin-authored cases stored in the `eval_cases` table, added through the
    Admin > Eval Cases tab without touching code. An admin supplies only prompt + criteria; the
    correct tool schema (if the agent needs one) is wired automatically from AGENT_TOOLS below, so
    a non-engineer never has to hand-write a tool_use JSON schema to add a real test.

industry_brief/competitor_brief/learning_agent cases make a real web_search/web_fetch call — that's
inherent to testing whether they actually cite real sources rather than fabricate (AGENT.md's
citation invariant), not an oversight; it does mean those specific cases are slower and not free.
"""

import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any

import anthropic

from agents.adapters.model_adapter import AGENT_MODELS
from agents.config import settings
from agents.contracts_graph import CONTRACTS_TOOLS
from agents.contracts_graph import MAX_ITERATIONS as CONTRACTS_MAX_ITERATIONS
from agents.eval_cases import list_eval_cases
from agents.loop_runner import ToolSpec, execute_tool_calls, extract_terminal_input, route_after_decide
from agents.nodes.ic_memo_drafter import IC_MEMO_MAX_ITERATIONS, IC_MEMO_TOOLS
from agents.nodes.pricing_advisor import PRICING_MAX_ITERATIONS, PRICING_TOOLS

DEFAULT_MODEL = "claude-sonnet-5"

# --- Trajectory-aware grading (agents/loop_runner.py agents only) ----------
# Each loop-enabled node module exports its own *_TOOLS constant specifically
# so this file can import and dispatch to the SAME tool schemas as
# production, rather than duplicating them the way RISK_FLAGGER_TOOL/
# CLAUSE_TOOL below are duplicated for single-shot agents — for a trajectory
# eval, the tool set being graded must be the real one, or the sequence
# being checked is meaningless.
TRAJECTORY_AGENTS = {"contracts_lead", "ic_memo_drafter", "pricing_advisor"}

TRAJECTORY_TOOLS: dict[str, list[ToolSpec]] = {
    "contracts_lead": CONTRACTS_TOOLS,
    "ic_memo_drafter": IC_MEMO_TOOLS,
    "pricing_advisor": PRICING_TOOLS,
}

TRAJECTORY_MAX_ITERATIONS: dict[str, int] = {
    "contracts_lead": CONTRACTS_MAX_ITERATIONS,
    "ic_memo_drafter": IC_MEMO_MAX_ITERATIONS,
    "pricing_advisor": PRICING_MAX_ITERATIONS,
}

# --- Tool schemas -----------------------------------------------------------
# Duplicated from each agent's own node module rather than imported, same
# precedent RISK_FLAGGER_TOOL already set here: eval fixtures stay self-
# contained so a node-internal refactor can't silently change what an eval
# actually exercises.

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

CLAUSE_TOOL = {
    "name": "report_clauses",
    "description": "Report the key clauses extracted from this contract.",
    "input_schema": {
        "type": "object",
        "properties": {
            "clauses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "required": ["label", "text"],
                },
            }
        },
        "required": ["clauses"],
    },
}

ANSWER_TOOL = {
    "name": "answer_question",
    "description": "Answer the user's question about this deal, grounded in the provided data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["answer", "sources"],
    },
}

ROUTE_TOOL = {
    "name": "route",
    "description": "Decide which Lead should handle this chat message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "route": {
                "type": "string",
                "enum": [
                    "concierge_qa",
                    "analyst_lead",
                    "contracts_lead",
                    "drafting_lead",
                    "web_research",
                    "update_stage",
                ],
            }
        },
        "required": ["route"],
    },
}

SYNTHESIS_TOOL = {
    "name": "report_knowledge_records",
    "description": "Report the structured knowledge records synthesized from this closed deal, grounded only in the real deal data provided.",
    "input_schema": {
        "type": "object",
        "properties": {
            "evaluation_approach": {
                "type": "object",
                "properties": {
                    "user_decisions": {"type": "string"},
                    "evaluation_methodology": {"type": "string"},
                    "outcome_comments": {"type": "string"},
                },
                "required": ["user_decisions", "evaluation_methodology", "outcome_comments"],
            },
            "analysis_approach": {
                "type": "object",
                "properties": {
                    "data_weighted": {"type": "string"},
                    "what_was_flagged": {"type": "string"},
                },
                "required": ["data_weighted", "what_was_flagged"],
            },
            "strategy_planning_approach": {
                "type": "object",
                "properties": {"description": {"type": "string"}},
                "required": ["description"],
            },
            "risk_signals_resolution": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "risk": {"type": "string"},
                        "materialized": {"type": "string", "enum": ["yes", "no", "unknown"]},
                        "resolution": {"type": "string"},
                    },
                    "required": ["risk", "materialized", "resolution"],
                },
            },
        },
        "required": ["evaluation_approach", "analysis_approach", "strategy_planning_approach", "risk_signals_resolution"],
    },
}

_DIGEST_AGENT_NAMES = [name for name in AGENT_MODELS if name != "learning_agent"]

DIGEST_TOOL = {
    "name": "report_digest",
    "description": "Report the research digest and, only if warranted, propose a specific skill improvement for one agent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "digest": {"type": "string"},
            "propose_skill_update": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string", "enum": _DIGEST_AGENT_NAMES},
                    "specific_gap": {"type": "string"},
                    "generality_check": {"type": "string"},
                    "additional_skill_instruction": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "agent_name",
                    "specific_gap",
                    "generality_check",
                    "additional_skill_instruction",
                    "rationale",
                ],
            },
        },
        "required": ["digest"],
    },
}

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
WEB_FETCH_TOOL = {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 5}
WEB_FETCH_BETAS = ["web-fetch-2025-09-10"]

# The tool set (if any) every case for a given agent uses by default — an
# admin adding a case via the Eval Cases tab never has to specify this; only
# a built-in case that deliberately targets a different real call path for
# the same agent_name (see the "web_research" case under "orchestrator"
# below) overrides it per-case.
AGENT_TOOLS: dict[str, list[dict]] = {
    "risk_flagger": [RISK_FLAGGER_TOOL],
    "clause_extractor": [CLAUSE_TOOL],
    "concierge_qa": [ANSWER_TOOL],
    "orchestrator": [ROUTE_TOOL],
    "knowledge_promoter": [SYNTHESIS_TOOL],
    "industry_brief": [WEB_SEARCH_TOOL, WEB_FETCH_TOOL],
    "competitor_brief": [WEB_SEARCH_TOOL, WEB_FETCH_TOOL],
    "learning_agent": [WEB_SEARCH_TOOL, WEB_FETCH_TOOL, DIGEST_TOOL],
}

AGENT_BETAS: dict[str, list[str]] = {
    "industry_brief": WEB_FETCH_BETAS,
    "competitor_brief": WEB_FETCH_BETAS,
    "learning_agent": WEB_FETCH_BETAS,
}

AGENT_MAX_TOKENS: dict[str, int] = {
    "clause_extractor": 2048,
    "knowledge_promoter": 2048,
    "industry_brief": 2048,
    "competitor_brief": 2048,
    "learning_agent": 4096,
    "drafting_lead": 512,
}

# --- Built-in eval cases -----------------------------------------------------

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
        {
            # Trajectory case for the new agentic loop (agents/nodes/pricing_advisor.py):
            # tests the degrade-gracefully contract's spirit — the agent must still
            # call report_pricing_note even when search_knowledge doesn't hand it
            # anything decisive, rather than fabricating precision the summary alone
            # doesn't support. (Deterministically forcing search_knowledge to fail is
            # out of scope here — that needs test-double tool injection this eval
            # harness doesn't have yet — so this checks the degrade behavior via
            # rubric, not a literal circuit-breaker trip.)
            "prompt": (
                "You are the Analyst Lead's pricing advisor. Based on the summary below, suggest "
                "indicative pricing ONLY if the data supports it. If comparable-deal pricing "
                "precedent would help, call search_knowledge — but if it returns nothing useful, do "
                "not let that block you: still call report_pricing_note with your best judgment from "
                "the summary alone (or insufficient_data: true if the summary alone isn't enough).\n\n"
                "SUMMARY:\nTarget company reported FY2025 revenue of 45M THB with no further detail."
            ),
            "trajectory_rubric": (
                "The agent should call report_pricing_note by the end of the trajectory, and should "
                "not fabricate a precise pricing figure from revenue alone with no margin/multiple "
                "data — either decline with insufficient_data or clearly caveat the suggestion."
            ),
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
        {
            # Trajectory case for the new agentic loop (agents/nodes/ic_memo_drafter.py):
            # a comparable-deal precedent signal is planted in the prompt itself so a
            # reasonable agent would want to check it before drafting the recommendation.
            "prompt": (
                "You are the Analyst Lead's IC memo drafter. Draft a concise IC memo in markdown "
                "from the summary and risk flags below. If comparable-deal precedent would "
                "materially strengthen the recommendation, call search_knowledge first. When done, "
                "call report_ic_memo.\n\nSUMMARY:\nTarget is a healthcare logistics company with "
                "FY2025 revenue of 90M THB and a proposed valuation of 9x EBITDA — unusually high "
                "for this sector; comparable precedent from past deals would help justify or "
                "challenge this multiple in the recommendation.\n\nRISK FLAGS:\n- [medium] Proposed "
                "valuation multiple has no cited comparable-transaction basis in the source "
                "documents."
            ),
            "trajectory_rubric": (
                "The agent should call search_knowledge to check comparable-deal pricing precedent "
                "before calling report_ic_memo, given the flagged risk about an unjustified "
                "valuation multiple, and the final memo should address that multiple."
            ),
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
        },
    ],
    "doc_summarizer": [
        {
            "prompt": (
                "You are the Analyst Lead's document summarizer for an M&A due diligence review. "
                "Summarize this document for an analyst: cover the key financial figures, notable "
                "risks or red flags, and any items that appear missing or outstanding. Be concrete "
                "— cite specific numbers and clauses where present. Keep it to a few tight "
                "paragraphs, not a bullet dump.\n\nDOCUMENT TEXT:\nFY2025 audited financials show "
                "revenue of 85M THB (up from 60M THB in FY2024) and net margin of 9%. Section 7.2 "
                "discloses an unresolved tax assessment of 4.2M THB currently under appeal with the "
                "Revenue Department. No customer concentration data was provided."
            ),
            "criteria": "Should cite the specific revenue figures (85M/60M THB) and the specific unresolved tax assessment (4.2M THB), and note the missing customer concentration data — not a vague, generic summary.",
        },
        {
            "prompt": (
                "You are the Analyst Lead's document summarizer for an M&A due diligence review. "
                "Summarize this document for an analyst: cover the key financial figures, notable "
                "risks or red flags, and any items that appear missing or outstanding. Be concrete "
                "— cite specific numbers and clauses where present.\n\nDOCUMENT TEXT:\nThis is a "
                "one-page cover letter accompanying a data room index. It contains no financial "
                "figures, no risk disclosures, and no clause text of any kind."
            ),
            "criteria": "Should plainly note that no financial figures or risk disclosures are present in this document, NOT invent figures or risks that aren't there.",
        },
    ],
    "contract_summarizer": [
        {
            "prompt": (
                "You are the Contracts Lead's contract summarizer. Summarize this contract for an "
                "analyst: the parties, the core commercial terms, the term/renewal structure, and "
                "anything unusual (change-of-control provisions, exclusivity, non-standard "
                "liability terms). Keep it to a few tight paragraphs.\n\nCONTRACT TEXT:\nThis "
                "Master Services Agreement between Siam Logistics Co. and Northbridge Health Group "
                "runs for an initial 3-year term with automatic 1-year renewals. Section 12 grants "
                "Northbridge the unilateral right to terminate immediately, without cause or "
                "counterparty consent, upon any change of control of Siam Logistics. Section 15 "
                "grants Northbridge exclusive rights to Siam's logistics services in Thailand."
            ),
            "criteria": "Should explicitly mention both the change-of-control termination right (Section 12) and the exclusivity provision (Section 15) as unusual/notable terms.",
        },
        {
            "prompt": (
                "You are the Contracts Lead's contract summarizer. Summarize this contract for an "
                "analyst: the parties, the core commercial terms, the term/renewal structure, and "
                "anything unusual. Keep it to a few tight paragraphs.\n\nCONTRACT TEXT:\nThis is a "
                "standard 12-month office lease between Landlord Co. and Tenant Ltd. at market "
                "rate, with a standard 30-day termination-for-cause clause and no other notable "
                "provisions."
            ),
            "criteria": "Should describe the parties and standard terms plainly WITHOUT inventing an unusual/notable clause that isn't actually present in this boilerplate lease.",
        },
    ],
    "clause_extractor": [
        {
            "prompt": (
                "You are the Contracts Lead's clause extractor. Extract the key clauses from this "
                "contract — term/renewal, termination, change-of-control, liability/"
                "indemnification, exclusivity, and any other clause a due-diligence analyst would "
                "need to know about. Call report_clauses with the result.\n\nCONTRACT TEXT:\n"
                "Section 9 (Change of Control): Either party may terminate this Agreement upon "
                "thirty (30) days' written notice if the other party undergoes a change of control, "
                "without further liability. Section 14 (Liability Cap): Each party's aggregate "
                "liability under this Agreement shall not exceed the fees paid in the twelve (12) "
                "months preceding the claim."
            ),
            "criteria": "The extracted clauses should include one labeled about change-of-control (quoting or closely paraphrasing the 30-day termination right) and one about the liability cap.",
        },
    ],
    "contracts_lead": [
        {
            # Trajectory case for the new agentic loop (agents/contracts_graph.py):
            # verifies search_knowledge gets called before the model finishes, on a
            # contract that plausibly warrants precedent-checking.
            "prompt": (
                "You are the Contracts Lead. Summarize this contract for an analyst and extract its "
                "key clauses. If comparable-deal precedent would help you judge whether a term is "
                "standard or unusual, call search_knowledge first. When you are done, call "
                "report_contract_analysis.\n\nCONTRACT TEXT:\nThis Master Services Agreement between "
                "Siam Logistics Co. and Northbridge Health Group grants Northbridge an unusually broad "
                "unilateral termination right upon any change of control of Siam Logistics, with no "
                "cure period and no counterparty consent required — assess whether this is standard "
                "market practice for logistics MSAs before finalizing your analysis."
            ),
            "expected_tool_sequence": ["search_knowledge", "report_contract_analysis"],
        },
        {
            # Adversarial: near-empty content gives the model nothing worth
            # searching for or reasoning about — verifies max_iterations is
            # respected (the model still finishes) rather than the loop
            # spinning on repeated tool calls.
            "prompt": (
                "You are the Contracts Lead. Summarize this contract for an analyst and extract its "
                "key clauses. When you are done, call report_contract_analysis.\n\nCONTRACT TEXT:\n"
                "(blank page — no text was extracted from this document)"
            ),
            "trajectory_rubric": (
                "The agent should still call report_contract_analysis within the iteration budget "
                "(plainly noting there's no real content to summarize or extract clauses from), "
                "rather than looping indefinitely or getting truncated."
            ),
        },
    ],
    "concierge_qa": [
        {
            "prompt": (
                "You are Concierge, the Kuvera Assistant's internal Q&A agent. You answer questions "
                "about EXACTLY ONE deal. The DEAL DATA given with each question is everything known "
                "about that deal — ground your answer only in it. If the answer isn't contained in "
                "the deal data, say so plainly rather than guessing. Call answer_question with your "
                "result.\n\nDEAL DATA:\nDeal: Project Riverstone. Stage: Due Diligence. Risk flags: "
                "[high] Change-of-control clause in the primary MSA allows the counterparty to "
                "terminate without consent. Milestones: NDA signed 2026-05-01.\n\nQUESTION: What is "
                "the highest-severity risk flagged on this deal so far?"
            ),
            "criteria": "Should answer that the change-of-control clause is the high-severity risk, citing the MSA/risk flag as a source, not a generic non-answer.",
        },
        {
            "prompt": (
                "You are Concierge, the Kuvera Assistant's internal Q&A agent. You answer questions "
                "about EXACTLY ONE deal. The DEAL DATA given with each question is everything known "
                "about that deal — ground your answer only in it. If the answer isn't contained in "
                "the deal data, say so plainly rather than guessing. Call answer_question with your "
                "result.\n\nDEAL DATA:\nDeal: Project Riverstone. Stage: Due Diligence. Risk flags: "
                "[high] Change-of-control clause in the primary MSA.\n\nQUESTION: What was the "
                "target company's EBITDA margin last year?"
            ),
            "criteria": "Should say plainly that this isn't contained in the deal data, NOT invent or guess an EBITDA margin figure.",
        },
    ],
    "orchestrator": [
        {
            "prompt": (
                "Classify this chat message about a specific deal. Call route with your decision.\n\n"
                "MESSAGE: Draft the IC memo for this deal."
            ),
            "criteria": "Should route to 'drafting_lead', since the user is asking to draft/generate an IC memo artifact.",
        },
        {
            "prompt": (
                "Classify this chat message about a specific deal. Call route with your decision.\n\n"
                "MESSAGE: What's the current highest-severity risk on this deal?"
            ),
            "criteria": "Should route to 'concierge_qa', since this asks to recall already-known data about this deal, not re-run analysis.",
        },
        {
            "prompt": (
                "Classify this chat message about a specific deal. Call route with your decision.\n\n"
                "MESSAGE: Look up Medtronic's latest 10-K filing."
            ),
            "criteria": "Should route to 'web_research', since this requires current external/public information, not this deal's own records.",
        },
        {
            # orchestrator's agent_configs row also governs agents/nodes/web_research.py
            # (it calls call_model("orchestrator", ...) directly, sharing skill_content/
            # model_id) — a skill change proposed for "orchestrator" is live for both the
            # routing classifier AND real web research on the very next call, so this case
            # exercises that second, easy-to-forget real call path under the same agent_name.
            "prompt": (
                "You are the Analyst Lead's research assistant. Answer the question below using "
                "web search for current, real-world information. Cite what you find. Keep the "
                "answer concise.\n\nQUESTION: What industry is Medtronic primarily known for?"
            ),
            "criteria": "Should ground the answer in real web search results (e.g. medical devices/healthcare technology), not fabricate an answer without searching.",
            "tools": [WEB_SEARCH_TOOL, WEB_FETCH_TOOL],
            "betas": WEB_FETCH_BETAS,
        },
    ],
    "knowledge_promoter": [
        {
            "prompt": (
                "You are the Knowledge Agent, promoting a closed deal's real history into "
                "firm-wide knowledge for future deals. Everything below is real data from this one "
                "deal — do not invent facts not present in it. If a field has no real basis in the "
                "data, say so plainly rather than guessing. Call report_knowledge_records.\n\n"
                "DEAL DATA:\nDeal: Project Riverstone. Risk flags identified during evaluation: "
                "[high] Change-of-control clause in the primary MSA allowing termination without "
                "consent. The deal closed successfully with no counterparty ever invoking that "
                "clause.\n\nOUTCOME: won"
            ),
            "criteria": "risk_signals_resolution should reference the change-of-control risk with materialized='no', grounded in the given outcome — not a fabricated or unrelated risk.",
        },
        {
            "prompt": (
                "You are the Knowledge Agent, promoting a closed deal's real history into "
                "firm-wide knowledge for future deals. Everything below is real data from this one "
                "deal — do not invent facts not present in it. If a field has no real basis in the "
                "data, say so plainly rather than guessing. Call report_knowledge_records.\n\n"
                "DEAL DATA:\nDeal: Project Thinfile. No tasks, notes, analysis, or risk flags were "
                "ever recorded for this deal.\n\nOUTCOME: lost"
            ),
            "criteria": "Fields like evaluation_methodology or what_was_flagged should say plainly there isn't enough data to determine this, NOT invent a plausible-sounding evaluation approach that was never recorded.",
        },
    ],
    "industry_brief": [
        {
            "prompt": (
                "You are the Knowledge Agent's industry analyst, writing a reference brief for M&A "
                "analysts. Research the renewable energy industry using web search for current, "
                "real information: recent news and notable company actions, trends, financial data, "
                "and your own assessment of investment-worthiness. Write a compact brief (3-5 "
                "paragraphs), citing what you actually find — no generic filler."
            ),
            "criteria": "Should contain specific, concrete facts, named companies, or figures drawn from real web research — not vague, generic industry filler that could apply to any sector.",
        },
    ],
    "competitor_brief": [
        {
            "prompt": (
                "You are the Knowledge Agent's competitor analyst, writing a reference brief for "
                "M&A analysts. Research Quintessa Northfield Dynamics Holdings (a real company in "
                "the quantum sensing industry, if it exists — say so plainly if you can't find real "
                "information rather than inventing any) using web search. Write a compact brief."
            ),
            "criteria": "Should say plainly it could not find real information about this company (which does not exist), NOT invent a plausible-sounding company history, financials, or news.",
        },
    ],
    "learning_agent": [
        {
            "prompt": (
                "You are the Learning Agent, continuously researching the outside world for an "
                "M&A deal-ops platform. Research current business, economic, and stock-market news, "
                "specifically: general market sentiment this week. Use web_search to find "
                "candidates, then web_fetch the most promising results.\n\nThen decide: does this "
                "research surface something CONCRETE and SPECIFIC enough to warrant adding ONE real "
                "instruction to a specific agent's skill.md? Only call propose_skill_update if ALL "
                "of the following hold — a specific concrete gap, general enough to matter beyond "
                "one deal, a specific instruction you can state, corroborated by more than one "
                "independent source. Most research cycles should NOT propose anything — omit "
                "propose_skill_update entirely if the bar isn't cleared. Call report_digest with "
                "your result."
            ),
            "criteria": "For a vague, non-specific topic like general market sentiment, the output should omit propose_skill_update entirely (digest only) rather than proposing a speculative skill change just because a tool call was expected.",
        },
    ],
    "drafting_lead": [
        {
            "prompt": (
                "You are the Drafting Lead's doc/email prep agent. Draft a short, professional "
                "cover email an M&A associate would send when circulating the attached IC memo to "
                "an external party. Reference the deal by name and give a one-paragraph high-level "
                "summary — do not restate the full memo. Keep it under 150 words. Output only the "
                "email body text, no subject line, no signature block.\n\nDEAL: Project Riverstone "
                "(Client: Meridian Capital)\nIC MEMO DRAFT:\n# Project Riverstone — IC Memo\n\n"
                "## Summary\nTarget is a healthcare logistics company with FY2025 revenue of 85M "
                "THB. Key risk: a change-of-control clause in the primary MSA allows the "
                "counterparty to terminate without consent. Indicative pricing: 680-850M THB "
                "(8-10x EBITDA)."
            ),
            "criteria": "Should be under ~150 words, reference 'Project Riverstone' by name, contain no subject line or signature block, and summarize at a high level rather than restating the memo's full detail (e.g. should not reproduce the exact pricing range or full risk text verbatim).",
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


def _run_candidate(
    prompt: str,
    system: str,
    model_id: str,
    tools: list[dict] | None,
    betas: list[str] | None,
    max_tokens: int,
) -> str:
    kwargs: dict[str, Any] = {"model": model_id, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools

    client = _client()
    response = client.beta.messages.create(betas=betas, **kwargs) if betas else client.messages.create(**kwargs)

    for block in response.content:
        if block.type == "tool_use":
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


TRAJECTORY_JUDGE_PROMPT = """You are grading an AI agent's MULTI-STEP TRAJECTORY for an M&A
due-diligence platform's eval suite — not just its final output, but the sequence of tool calls
it made to get there. Be strict but fair.

RUBRIC: {rubric}

TOOL-CALL TRAJECTORY (in order):
{trajectory}

FINAL OUTPUT:
{output}

Does the trajectory and final output together satisfy the rubric? Respond with exactly PASS or
FAIL on the first line, then a one-sentence reason on the second line."""

# A trajectory eval drives the loop harness directly against a synthetic
# prompt, same honest scope note as _run_candidate above: this exercises the
# agent's core prompt+skill+tool-choice behavior, not the full node pipeline
# (which needs a real document_id/deal_id an eval harness can't fabricate).
# Deliberately does NOT go through loop_runner.call_model_step() /
# agents.adapters.model_adapter.call_model() — those resolve the agent's
# LIVE, DB-stored config, but an eval must test the CANDIDATE skill_content/
# model_id being proposed, exactly like _run_candidate's own raw client call
# above bypasses call_model() for the same reason.
_TRAJECTORY_CIRCUIT_BREAKER_THRESHOLD = 2


def _run_trajectory_candidate(
    prompt: str,
    skill_content: str,
    model_id: str,
    tool_specs: list[ToolSpec],
    max_tokens: int,
    max_iterations: int,
) -> dict[str, Any]:
    messages: list[dict] = [{"role": "user", "content": prompt}]
    failure_counts: dict[str, int] = {}
    tripped: set[str] = set()
    side_effects: dict[str, str] = {}
    steps: list = []
    iteration = 0

    tools = [spec.schema for spec in tool_specs]
    terminal_name = next(spec.schema["name"] for spec in tool_specs if spec.terminal)

    while True:
        kwargs: dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens,
            "tools": tools,
            "messages": messages,
        }
        if skill_content:
            kwargs["system"] = skill_content
        response = _client().messages.create(**kwargs)
        messages = messages + [{"role": "assistant", "content": response.content}]
        iteration += 1

        route = route_after_decide(response, iteration, max_iterations, tool_specs)

        if route == "truncated":
            return {
                "result_kind": "truncated",
                "steps": [asdict(s) for s in steps],
                "final_output": None,
                "circuit_broken_tools": list(tripped),
            }

        if route == "finalize":
            result = extract_terminal_input(response, terminal_name)
            return {
                "result_kind": "circuit_broken" if tripped else "graded",
                "steps": [asdict(s) for s in steps],
                "final_output": json.dumps(result, default=str) if result is not None else "(no output)",
                "circuit_broken_tools": list(tripped),
            }

        tool_results, round_steps, _ = execute_tool_calls(
            response,
            tool_specs,
            failure_counts,
            tripped,
            side_effects,
            _TRAJECTORY_CIRCUIT_BREAKER_THRESHOLD,
            invocation_id=None,  # eval runs aren't real production invocations — nothing to log against
            step_offset=len(steps),
        )
        steps.extend(round_steps)
        messages = messages + [{"role": "user", "content": tool_results}]


def _grade_trajectory(
    rubric: str | None,
    expected_tool_sequence: list[str] | None,
    steps: list[dict],
    final_output: str | None,
) -> tuple[bool, str]:
    called_names = [s["tool_name"] for s in steps if s["status"] == "success"]

    if expected_tool_sequence:
        idx = 0
        for name in called_names:
            if idx < len(expected_tool_sequence) and name == expected_tool_sequence[idx]:
                idx += 1
        if idx < len(expected_tool_sequence):
            return (
                False,
                f"Expected tool sequence not fully satisfied (missing/out-of-order: "
                f"{expected_tool_sequence[idx:]}). Actual calls: {called_names or '(none)'}",
            )
        if not rubric:
            return True, f"Tool sequence satisfied: {called_names or '(none)'}"

    if rubric:
        trajectory_desc = "\n".join(f"{i + 1}. {s['tool_name']} -> {s['status']}" for i, s in enumerate(steps))
        response = _client().messages.create(
            model=DEFAULT_MODEL,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": TRAJECTORY_JUDGE_PROMPT.format(
                        rubric=rubric,
                        trajectory=trajectory_desc or "(no tool calls)",
                        output=final_output or "(no output)",
                    ),
                }
            ],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        first_line = text.split("\n")[0].upper()
        return first_line.startswith("PASS"), text

    return True, f"Tool sequence satisfied: {called_names or '(none)'}"


def run_eval(agent_name: str, skill_content: str, model_id: str = DEFAULT_MODEL) -> dict[str, Any]:
    custom_cases = [
        {
            "prompt": c["prompt"],
            "criteria": c["criteria"],
            "expected_tool_sequence": c.get("expected_tool_sequence"),
            "trajectory_rubric": c.get("trajectory_rubric"),
            "max_iterations": c.get("max_iterations"),
        }
        for c in list_eval_cases(agent_name)
    ]
    cases = EVAL_CASES.get(agent_name, []) + custom_cases
    if not cases:
        return {"pass_rate": None, "results": [], "note": "No eval cases defined for this agent"}

    default_tools = AGENT_TOOLS.get(agent_name)
    default_betas = AGENT_BETAS.get(agent_name)
    max_tokens = AGENT_MAX_TOKENS.get(agent_name, 1024)

    trajectory_specs = TRAJECTORY_TOOLS.get(agent_name) if agent_name in TRAJECTORY_AGENTS else None
    default_max_iterations = TRAJECTORY_MAX_ITERATIONS.get(agent_name, 3)

    results = []
    excluded_kinds: list[str] = []

    for case in cases:
        is_trajectory_case = trajectory_specs is not None and (
            case.get("expected_tool_sequence") or case.get("trajectory_rubric")
        )

        if is_trajectory_case:
            run = _run_trajectory_candidate(
                case["prompt"],
                skill_content,
                model_id,
                trajectory_specs,
                max_tokens,
                case.get("max_iterations") or default_max_iterations,
            )
            if run["result_kind"] == "graded":
                passed, reason = _grade_trajectory(
                    case.get("trajectory_rubric"), case.get("expected_tool_sequence"), run["steps"], run["final_output"]
                )
            else:
                # A circuit-breaker trip or max_iterations truncation is an
                # infrastructure/guardrail signal, not an ordinary quality
                # miss — see Governance Wiring. Not graded PASS/FAIL; excluded
                # from pass_rate below, and reported as its own note.
                passed = False
                reason = (
                    f"Not graded — {run['result_kind']} (circuit_broken_tools={run['circuit_broken_tools']})"
                )
                excluded_kinds.append(run["result_kind"])
            results.append(
                {
                    "criteria": case.get("trajectory_rubric") or f"expected tool sequence: {case.get('expected_tool_sequence')}",
                    "output": (run["final_output"] or "")[:500],
                    "passed": passed,
                    "reason": reason,
                    "steps": run["steps"],
                    "result_kind": run["result_kind"],
                    "circuit_broken_tools": run["circuit_broken_tools"],
                }
            )
            continue

        tools = case.get("tools", default_tools)
        betas = case.get("betas", default_betas)
        output = _run_candidate(case["prompt"], skill_content, model_id, tools, betas, max_tokens)
        passed, reason = _grade(case["criteria"], output)
        results.append(
            {
                "criteria": case["criteria"],
                "output": output[:500],
                "passed": passed,
                "reason": reason,
                "result_kind": "graded",
            }
        )

    graded_results = [r for r in results if r["result_kind"] == "graded"]
    pass_rate = (sum(1 for r in graded_results if r["passed"]) / len(graded_results)) if graded_results else None

    payload: dict[str, Any] = {"pass_rate": pass_rate, "results": results}
    if excluded_kinds:
        payload["note"] = (
            f"{len(excluded_kinds)} case(s) hit the circuit breaker / max_iterations during this eval "
            f"run — pass_rate excludes them, see results for detail"
        )
    return payload
