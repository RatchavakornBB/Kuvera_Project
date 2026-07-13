"""Gathers everything known about ONE deal into a single text block for
Concierge Q&A. This is the actual enforcement of the deal_id scope
invariant (AGENT.md Section 11) — the prompt physically never contains
another deal's data, so there is nothing for the model to leak even if it
wanted to. Not real vector search: at this data scale (a handful of
records per deal) a full RAG/pgvector pipeline is premature complexity —
"lightweight RAG" here means direct context-stuffing (see decisions.md)."""

from agents.db import get_client


def build_deal_context(deal_id: str) -> str:
    client = get_client()

    deal_rows = client.table("deals").select("*, owner:users(full_name)").eq("id", deal_id).execute().data
    if not deal_rows:
        raise ValueError(f"No deal with id {deal_id}")
    deal = deal_rows[0]

    contacts = client.table("contacts").select("*").eq("deal_id", deal_id).execute().data
    documents = client.table("documents").select("*").eq("deal_id", deal_id).execute().data
    tasks = client.table("tasks").select("*").eq("deal_id", deal_id).execute().data
    notes = client.table("meeting_notes").select("*").eq("deal_id", deal_id).execute().data
    dd_items = client.table("dd_items").select("*").eq("deal_id", deal_id).execute().data
    milestones = (
        client.table("milestones").select("*").eq("deal_id", deal_id).order("sort_order").execute().data
    )
    analyses = (
        client.table("analyses")
        .select("*")
        .eq("deal_id", deal_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )

    lines = [
        f"DEAL: {deal['name']} (client: {deal['client']}, industries: {', '.join(deal['industries'])})",
        f"Stage: {deal['stage']} | Status: {deal['status']} | Owner: {(deal.get('owner') or {}).get('full_name', 'unassigned')}",
        "",
    ]

    if contacts:
        lines.append("CONTACTS:")
        for c in contacts:
            lines.append(f"- {c['name']} ({c.get('role') or 'role unknown'}) — last contacted {c.get('last_contacted_at') or 'never'}")
        lines.append("")

    if documents:
        lines.append("DOCUMENTS:")
        for d in documents:
            summary = f" — {d['summary'][:200]}" if d.get("summary") else " — no summary yet"
            lines.append(f"- {d['name']} [{d['type']}, status={d['status']}]{summary}")
            if d.get("clauses"):
                for clause in d["clauses"]:
                    lines.append(f"    clause [{clause['label']}]: {clause['text'][:150]}")
        lines.append("")

    if milestones:
        lines.append("MILESTONES:")
        for m in milestones:
            state = m["occurred_at"] or "not reached"
            lines.append(f"- {m['label']}: {state}")
        lines.append("")

    if tasks:
        lines.append("TASKS:")
        for t in tasks:
            lines.append(f"- {t['text']} (due {t.get('due_date') or 'no date'}, done={t['done']})")
        lines.append("")

    if dd_items:
        lines.append("DUE DILIGENCE CHECKLIST:")
        for item in dd_items:
            lines.append(f"- {item['item']}: {item['status']}")
        lines.append("")

    if notes:
        lines.append("MEETING NOTES:")
        for n in notes:
            lines.append(f"- {n['occurred_at']}: {n.get('summary') or '(no summary)'}")
        lines.append("")

    if analyses:
        a = analyses[0]
        lines.append("LATEST ANALYST LEAD OUTPUT:")
        lines.append(f"Summary: {a['summary']}")
        if a.get("risk_flags"):
            lines.append("Risk flags:")
            for r in a["risk_flags"]:
                lines.append(f"  - [{r['severity']}] {r['description']}")
        if a.get("ic_memo_draft"):
            lines.append(f"IC memo draft: {a['ic_memo_draft'][:500]}...")
        if a.get("pricing_note"):
            lines.append(f"Pricing note: {a['pricing_note']}")
        lines.append("")

    return "\n".join(lines)
