"""SEC EDGAR fetcher — system-architecture.md Section 5.3. No API key
needed, only a compliant User-Agent header per SEC's fair-use policy.
Hard-routed as a plain conditional in the Analyst Lead's tool-selection
step (not an LLM tool-use round trip) — this module is called directly by
Python code, never exposed to Claude as a callable tool.
"""

import re

import httpx

USER_AGENT = "Kuvera Capital contact@kuvera.capital"
FORM_TYPES = ("10-K", "10-Q", "20-F")


def _headers() -> dict:
    return {"User-Agent": USER_AGENT}


def lookup_cik(company_name_or_ticker: str) -> dict | None:
    """Step 1: CIK lookup by company name or ticker."""
    resp = httpx.get("https://www.sec.gov/files/company_tickers.json", headers=_headers(), timeout=15)
    resp.raise_for_status()
    tickers = resp.json()

    needle = company_name_or_ticker.strip().lower()
    for entry in tickers.values():
        if entry["ticker"].lower() == needle or entry["title"].lower() == needle:
            return entry
    # Word-boundary match, not a bare substring — "look" must not match
    # inside "Outlook Therapeutics" (this exact false-positive was caught
    # via a real end-to-end test, see phase3-006's report).
    pattern = re.compile(r"\b" + re.escape(needle) + r"\b")
    for entry in tickers.values():
        if pattern.search(entry["title"].lower()):
            return entry
    return None


def fetch_recent_filings(cik: int, limit: int = 5) -> list[dict]:
    """Step 2: filing fetch for that CIK, filtered to 10-K/10-Q/20-F."""
    padded_cik = str(cik).zfill(10)
    resp = httpx.get(
        f"https://data.sec.gov/submissions/CIK{padded_cik}.json", headers=_headers(), timeout=15
    )
    resp.raise_for_status()
    recent = resp.json()["filings"]["recent"]

    filings = []
    for i, form in enumerate(recent["form"]):
        if form in FORM_TYPES:
            filings.append(
                {
                    "form": form,
                    "filing_date": recent["filingDate"][i],
                    "accession_number": recent["accessionNumber"][i],
                    "primary_document": recent["primaryDocument"][i],
                }
            )
        if len(filings) >= limit:
            break
    return filings


def fetch_company_filings(company_name_or_ticker: str, limit: int = 5) -> dict | None:
    """The combined two-step call the Analyst Lead actually uses."""
    entry = lookup_cik(company_name_or_ticker)
    if entry is None:
        return None
    filings = fetch_recent_filings(entry["cik_str"], limit=limit)
    return {"company": entry["title"], "ticker": entry["ticker"], "cik": entry["cik_str"], "filings": filings}
