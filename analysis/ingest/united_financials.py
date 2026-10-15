"""Manchester United plc financials from SEC EDGAR (Form 20-F XBRL facts).

Why EDGAR: since the 2012 NYSE listing, United files audited annual accounts
with the SEC, and the XBRL "company facts" API gives them as clean numbers.
Machine-readable (XBRL) data only exists from the FY2018 filing, which also
restates the two prior years, so coverage is roughly FY2016 onward. Earlier
years are logged in DATA_GAPS.md rather than typed in by hand.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from analysis.clean.seasons import fiscal_year_to_season
from analysis.ingest.http import fetch

COMPANY_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001549107.json"
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"

# Our column name -> XBRL tags in priority order (United switched revenue tags in 2019).
FLOW_TAGS: dict[str, list[str]] = {
    "revenue": ["RevenueFromContractsWithCustomers", "Revenue"],
    "wages": ["EmployeeBenefitsExpense"],
    "interest_paid": ["InterestPaidClassifiedAsOperatingActivities"],
    "dividends_paid": ["DividendsPaidClassifiedAsFinancingActivities", "DividendsPaid"],
    "debt_issue_costs": ["PaymentsForDebtIssueCosts"],
    "player_purchases_cash": ["PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities"],
    "amortisation": ["AmortisationIntangibleAssetsOtherThanGoodwill"],
    "operating_profit": ["ProfitLossFromOperatingActivities"],
    "profit_loss": ["ProfitLoss"],
}
STOCK_TAGS: dict[str, list[str]] = {
    "net_debt": ["NetDebt"],
    "borrowings": ["Borrowings"],
    "cash": ["CashAndCashEquivalents"],
}


def _fy_end_year(end: str) -> int | None:
    day = dt.date.fromisoformat(end)
    # United's year ends 30 June; anything else is an interim/odd period.
    return day.year if day.month == 6 and day.day == 30 else None


def _annual_values(fact: dict, gbp_only: bool, is_flow: bool) -> dict[int, float]:
    """One value per FY. Later filings win, so restatements replace originals."""
    values: dict[int, tuple[str, float]] = {}
    units = fact["units"].get("GBP") if gbp_only else next(iter(fact["units"].values()))
    for item in units or []:
        if not str(item.get("form", "")).startswith("20-F"):
            continue
        fy = _fy_end_year(item["end"])
        if fy is None:
            continue
        if is_flow:
            start = dt.date.fromisoformat(item["start"])
            if (dt.date.fromisoformat(item["end"]) - start).days < 350:
                continue  # skip quarters / half-years
        filed = item.get("filed", "")
        if fy not in values or filed > values[fy][0]:
            values[fy] = (filed, float(item["val"]))
    return {fy: v for fy, (_, v) in values.items()}


def parse_company_facts(raw: bytes) -> pd.DataFrame:
    facts = json.loads(raw)["facts"]["ifrs-full"]
    table: dict[int, dict[str, float]] = {}
    for col, tags, is_flow in [(c, t, True) for c, t in FLOW_TAGS.items()] + [(c, t, False) for c, t in STOCK_TAGS.items()]:
        for tag in tags:
            if tag not in facts:
                continue
            for fy, val in _annual_values(facts[tag], True, is_flow).items():
                table.setdefault(fy, {}).setdefault(col, val)
    df = pd.DataFrame.from_dict(table, orient="index").sort_index()
    df.index.name = "fy_end_year"
    df = df.reset_index()
    df["season"] = df["fy_end_year"].map(fiscal_year_to_season)
    # Cash-flow lines are reported as positive outflows in some years and
    # negative in others depending on tag; store outflows as positive numbers.
    for col in ["interest_paid", "dividends_paid", "debt_issue_costs", "player_purchases_cash"]:
        if col in df:
            df[col] = df[col].abs()
    return df


def main() -> None:
    raw = fetch(COMPANY_FACTS, "sec_edgar", refresh=False)
    if raw is None:
        raise SystemExit("EDGAR unavailable")
    df = parse_company_facts(raw)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "united_financials.parquet", index=False)
    pd.set_option("display.width", 250)
    print((df.set_index("fy_end_year") / 1e6).round(1).drop(columns="season").to_string())


if __name__ == "__main__":
    main()
