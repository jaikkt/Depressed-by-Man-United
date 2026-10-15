"""Spending efficiency: how many points should a club's resources buy?

Model (fitted on every PL club-season, not just United):
    PPG = a + b * log(resource / league-average resource that season)
Using resources *relative to the league average* removes football's huge
wage/fee inflation, so 2005 and 2025 are comparable without guessing a
football-specific deflator.

Which resource? The thesis is about wages, but no open dataset has the wage
bill of every PL club for every season (we searched; Deloitte/Capology data is
paywalled). So the primary model uses Transfermarkt squad market value, which
exists for every club from 2004-05 and tracks wage bills closely. If a
hand-compiled `data/manual/club_wages.csv` (season, team, wages_gbp) is added
from published accounts, the same code fits the true wage model.

A residual is actual PPG minus model PPG; we also convert it into league
places using that season's own PPG-by-position curve.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis.clean.tables import ppg_to_position
from analysis.clean.teams import BIG_SIX, UNITED

MANUAL_WAGES = Path(__file__).resolve().parents[1] / "data" / "manual" / "club_wages.csv"


@dataclass
class ResourceModel:
    resource: str
    intercept: float
    slope: float
    r2: float
    n: int
    seasons: tuple[int, int]


def relative_resource(df: pd.DataFrame, col: str) -> pd.DataFrame:
    out = df.dropna(subset=[col]).copy()
    out = out[out[col] > 0]
    out["rel"] = out[col] / out.groupby("season")[col].transform("mean")
    out["log_rel"] = np.log(out["rel"])
    return out


def fit_resource_model(df: pd.DataFrame, resource: str, exclude_seasons: set[int] = frozenset()) -> tuple[ResourceModel, pd.DataFrame]:
    """`df` has season, team, ppg, position and the resource column."""
    data = relative_resource(df, resource)
    train = data[~data["season"].isin(exclude_seasons)]
    X = sm.add_constant(train["log_rel"])
    ols = sm.OLS(train["ppg"], X).fit()
    data["pred_ppg"] = ols.params["const"] + ols.params["log_rel"] * data["log_rel"]
    data["residual"] = data["ppg"] - data["pred_ppg"]
    model = ResourceModel(resource=resource, intercept=float(ols.params["const"]), slope=float(ols.params["log_rel"]),
                          r2=float(ols.rsquared), n=int(len(train)),
                          seasons=(int(train["season"].min()), int(train["season"].max())))
    return model, data


def add_place_residuals(data: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """places_vs_model > 0 means the club finished *higher* than its money predicts."""
    out = data.copy()
    expected = []
    for row in out.itertuples(index=False):
        expected.append(ppg_to_position(row.pred_ppg, table[table["season"] == row.season]))
    out["expected_position"] = expected
    out["places_vs_model"] = out["expected_position"] - out["position"]
    return out


def club_summary(data: pd.DataFrame, clubs: list[str] = BIG_SIX) -> pd.DataFrame:
    sub = data[data["team"].isin(clubs)]
    return sub.groupby("team").agg(
        seasons=("season", "size"), mean_residual_ppg=("residual", "mean"),
        total_points_vs_model=("residual_points", "sum"), mean_places_vs_model=("places_vs_model", "mean"),
    ).reset_index().sort_values("mean_residual_ppg")


def load_manual_wages() -> pd.DataFrame | None:
    if not MANUAL_WAGES.exists():
        return None
    return pd.read_csv(MANUAL_WAGES)


def net_spend_by_club_season(transfers: pd.DataFrame) -> pd.DataFrame:
    """Known fees only (unknown fees are excluded, never treated as zero).
    Expects a fee_gbp_real column."""
    t = transfers[~transfers["is_loan"]].dropna(subset=["fee_gbp_real"])
    spend = t[t["direction"] == "in"].groupby(["season", "team"])["fee_gbp_real"].sum().rename("spend")
    sales = t[t["direction"] == "out"].groupby(["season", "team"])["fee_gbp_real"].sum().rename("sales")
    out = pd.concat([spend, sales], axis=1).fillna(0.0).reset_index()
    out["net_spend"] = out["spend"] - out["sales"]
    return out


def united_glazer_outflows(fin: pd.DataFrame) -> pd.DataFrame:
    """Money leaving the club to service the 2005 leveraged buyout: interest,
    dividends and debt-related fees, by financial year (where filed in XBRL)."""
    cols = ["fy_end_year", "season", "interest_paid", "dividends_paid", "debt_issue_costs", "net_debt", "borrowings", "revenue", "wages"]
    out = fin[[c for c in cols if c in fin.columns]].copy()
    # Missing stays missing: a line absent from a filing is not proof it was zero.
    out["wages_to_revenue"] = out["wages"] / out["revenue"]
    return out


UNITED_SLUG = UNITED
