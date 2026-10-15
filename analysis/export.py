"""Run every model and write the website's JSON (web/public/data/).

    analysis/.venv/bin/python -m analysis.export

Inputs are the parquet files the ingest modules wrote to data/processed/.
Outputs: one JSON per screen + sources.json, the generated TypeScript types
(web/lib/data-types.ts) and analysis/DATA_GAPS.md (regenerated each run, so
the coverage numbers in it are always current).
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analysis import schema
from analysis.clean.money import eur_to_gbp, to_real
from analysis.clean.seasons import current_season_start, games_per_season, season_label
from analysis.clean.tables import league_table, team_match_log
from analysis.clean.teams import BIG_SIX, COMPARISON, DISPLAY, UNITED
from analysis.ingest import clubelo
from analysis.ingest.cpi import load_season_index
from analysis.ingest.fx import load_gbp_per_eur
from analysis.ingest.results import load_warmup
from analysis.models import changepoint, clustering, manager_bounce, manager_eras, monte_carlo, transfer_roi
from analysis.models import wage_regression as wr
from analysis.models.dixon_coles import DCParams, fit
from analysis.models.elo import run_elo

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "analysis" / "data" / "processed"
MANUAL = ROOT / "analysis" / "data" / "manual"
WEB_DATA = ROOT / "web" / "public" / "data"
WEB_TYPES = ROOT / "web" / "lib" / "data-types.ts"
MANAGERS_DIR = ROOT / "web" / "public" / "managers"
GAPS_FILE = ROOT / "analysis" / "DATA_GAPS.md"
MAX_BYTES = 300_000

TODAY = dt.date.today().isoformat()
CURRENT = current_season_start()


# ---------- helpers --------------------------------------------------------------

def clean(obj: Any) -> Any:
    """Make data JSON-safe: numpy -> python, NaN/inf -> None, round floats."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, dt.date)):
        return obj.strftime("%Y-%m-%d")
    if obj is pd.NaT:
        return None
    return obj


def opt(v: Any) -> Any:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def display(team: str) -> str:
    return DISPLAY.get(team, team.replace("-", " ").title())


def money(v: float | None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "NO DATA"
    sign = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e9:
        return f"{sign}£{a / 1e9:.2f}bn"
    return f"{sign}£{a / 1e6:.0f}m"


def read(name: str) -> pd.DataFrame | None:
    p = PROCESSED / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else None


# ---------- load everything ------------------------------------------------------

class Data:
    def __init__(self) -> None:
        self.results = read("results")
        if self.results is None:
            raise SystemExit("Run analysis.ingest.results first")
        self.results["date"] = pd.to_datetime(self.results["date"])
        self.table = league_table(self.results)
        self.log = team_match_log(self.results)
        self.gps = {int(s): int(g) for s, g in self.table.groupby("season")["played"].max().items()}
        for s in self.gps:
            self.gps[s] = games_per_season(s)
        self.cpi = load_season_index()
        self.rates = load_gbp_per_eur()
        self.overview = read("tm_league_overview")
        self.transfers = read("tm_transfers")
        self.coaches = read("tm_coaches")
        self.squad = read("tm_squad_stats")
        self.starters = read("united_starters")
        self.tm_fixtures = read("united_tm_fixtures")
        self.fin = read("united_financials")

        if self.transfers is not None:
            t = self.transfers
            t["fee_gbp_real"] = to_real(eur_to_gbp(t["fee_eur"], t["season"], self.rates), t["season"], self.cpi)
        if self.overview is not None:
            o = self.overview
            o["squad_value_gbp_real"] = to_real(eur_to_gbp(o["squad_value_eur"], o["season"], self.rates), o["season"], self.cpi)

        warm = load_warmup()
        warm["date"] = pd.to_datetime(warm["date"])
        elo_all = run_elo(pd.concat([warm, self.results], ignore_index=True))
        self.elo = elo_all[elo_all["season"] >= 1992].reset_index(drop=True)
        self.clubelo = clubelo.load_all()

        self.united_log = self.log[self.log["team"] == UNITED].sort_values("date").reset_index(drop=True)
        self.united_elo = self.elo[self.elo["team"] == UNITED].sort_values("date").reset_index(drop=True)
        mgr = pd.read_csv(MANUAL / "united_managers.csv", parse_dates=["start", "end"])
        mgr["interim"] = mgr["interim"].eq("yes")
        self.united_managers = mgr
        self.trophies = pd.read_csv(MANUAL / "united_trophies.csv", parse_dates=["date"])
        credits_path = MANAGERS_DIR / "credits.json"
        self.credits: list[dict[str, str]] = json.loads(credits_path.read_text()) if credits_path.exists() else []
        self.net_spend = wr.net_spend_by_club_season(self.transfers) if self.transfers is not None else pd.DataFrame()

    def manager_on(self, day: pd.Timestamp) -> str | None:
        m = self.united_managers
        hit = m[(m["start"] <= day) & ((m["end"].isna()) | (m["end"] > day))]
        return None if hit.empty else str(hit.iloc[-1]["slug"])


# ---------- simulate -------------------------------------------------------------

def market_xpts(results: pd.DataFrame) -> pd.DataFrame:
    """Expected points implied by bookmaker odds (overround removed by
    normalising). A stand-in for xG-based expected points, which needs data
    we could not source."""
    r = results.dropna(subset=["odds_h", "odds_d", "odds_a"])
    inv = 1 / r[["odds_h", "odds_d", "odds_a"]]
    p = inv.div(inv.sum(axis=1), axis=0)
    home = pd.DataFrame({"season": r["season"], "team": r["home"], "xpts": 3 * p["odds_h"] + p["odds_d"]})
    away = pd.DataFrame({"season": r["season"], "team": r["away"], "xpts": 3 * p["odds_a"] + p["odds_d"]})
    both = pd.concat([home, away])
    out = both.groupby(["season", "team"]).agg(xpts=("xpts", "sum"), n=("xpts", "size")).reset_index()
    return out


def subset_params(p: DCParams, teams: list[str]) -> DCParams:
    idx = p.index()
    keep = [idx[t] for t in teams]
    return DCParams(teams=teams, attack=p.attack[keep], defence=p.defence[keep], home_adv=p.home_adv, rho=p.rho)


def build_simulate(d: Data) -> tuple[dict[str, Any], pd.DataFrame]:
    xp = market_xpts(d.results)
    seasons = []
    summaries = []
    for season, games in d.results.groupby("season"):
        season = int(season)
        n_teams = games["home"].nunique()
        in_progress = len(games) < n_teams * (n_teams - 1)
        teams = sorted(set(games["home"]) | set(games["away"]))
        if in_progress:
            # Too few games to fit alone: add last season, down-weighted by time decay.
            prev = d.results[d.results["season"] == season - 1]
            params = subset_params(fit(pd.concat([prev, games]), xi=0.0019), teams)
            fixtures = monte_carlo.remaining_fixtures(games, teams)
            sim = monte_carlo.simulate_season(params, fixtures, fixed=games)
        else:
            # Finished season: every game counts equally when judging the season itself.
            params = fit(games, xi=0.0)
            fixtures = monte_carlo.remaining_fixtures(games.iloc[:0], teams)
            sim = monte_carlo.simulate_season(params, fixtures)
        summ = monte_carlo.summarise(sim)
        tab = d.table[d.table["season"] == season].set_index("team")
        sx = xp[xp["season"] == season].set_index("team")
        idx = params.index()
        team_rows = []
        for r in summ.itertuples(index=False):
            full_coverage = r.team in sx.index and int(sx.loc[r.team, "n"]) == int(tab.loc[r.team, "played"])
            team_rows.append({
                "team": r.team, "display": display(r.team),
                "actual_points": int(tab.loc[r.team, "pts"]), "actual_position": int(tab.loc[r.team, "position"]),
                "played": int(tab.loc[r.team, "played"]),
                "p5": r.p5, "p25": r.p25, "p50": r.p50, "p75": r.p75, "p95": r.p95,
                "mean_points": r.mean_points, "p_title": r.p_title, "p_top4": r.p_top4,
                "p_relegation": r.p_relegation, "exp_position": r.exp_position,
                "attack": float(np.exp(params.attack[idx[r.team]])), "defence": float(np.exp(params.defence[idx[r.team]])),
                "market_xpts": float(sx.loc[r.team, "xpts"]) if full_coverage else None,
            })
        team_rows.sort(key=lambda t: t["exp_position"])
        hist = monte_carlo.points_histogram(sim, UNITED) if UNITED in teams else {}
        seasons.append({
            "season": season, "label": season_label(season), "in_progress": in_progress,
            "matches_played": int(len(games)), "home_adv": float(np.exp(params.home_adv)), "rho": params.rho,
            "n_sims": monte_carlo.N_SIMS, "teams": team_rows,
            "united_hist": [{"points": k, "p": v} for k, v in sorted(hist.items())],
            "convergence": monte_carlo.convergence(sim, UNITED) if UNITED in teams else [],
        })
        summ["season"] = season
        summaries.append(summ)
        print(f"[simulate] {season_label(season)} done")
    return {"generated": TODAY, "seasons": seasons}, pd.concat(summaries, ignore_index=True)


# ---------- finances -------------------------------------------------------------

def build_finances(d: Data) -> tuple[dict[str, Any], pd.DataFrame]:
    base = d.table.merge(d.overview[["season", "team", "squad_value_gbp_real"]], on=["season", "team"], how="left")
    manual_wages = wr.load_manual_wages()
    if manual_wages is not None:
        base = base.merge(manual_wages, on=["season", "team"], how="left")
        resource, label = "wages_gbp", "Wage bill (published accounts)"
    else:
        resource, label = "squad_value_gbp_real", "Squad market value (Transfermarkt), wage proxy"
    model, data = wr.fit_resource_model(base, resource, exclude_seasons={CURRENT})
    data = wr.add_place_residuals(data, d.table)
    data["residual_points"] = data["residual"] * data["played"]
    summary = wr.club_summary(data[data["season"] < CURRENT])

    points = [{
        "season": int(r.season), "season_label": season_label(int(r.season)), "team": r.team, "rel": r.rel,
        "ppg": r.ppg, "pred_ppg": r.pred_ppg, "residual": r.residual, "position": int(r.position),
        "expected_position": r.expected_position, "places_vs_model": r.places_vs_model,
        "in_progress": bool(r.season == CURRENT and r.played < games_per_season(int(r.season))),
    } for r in data.itertuples(index=False)]

    ns = d.net_spend[d.net_spend["team"].isin(BIG_SIX)].merge(d.table[["season", "team", "pts"]], on=["season", "team"], how="left")
    net_rows = [{
        "team": r.team, "season": int(r.season), "season_label": season_label(int(r.season)),
        "spend": r.spend, "sales": r.sales, "net_spend": r.net_spend,
        "points": None if pd.isna(r.pts) else int(r.pts),
        "net_spend_per_point": None if pd.isna(r.pts) or r.pts == 0 else r.net_spend / r.pts,
    } for r in ns.sort_values(["team", "season"]).itertuples(index=False)]

    money_rows = []
    totals = None
    if d.fin is not None:
        g = wr.united_glazer_outflows(d.fin)
        g = g.dropna(subset=["revenue"])
        cpi = d.cpi.set_index("season")["to_latest"]
        for r in g.itertuples(index=False):
            f = float(cpi.get(int(r.season), cpi.iloc[-1]))
            pts_row = d.table[(d.table["season"] == r.season) & (d.table["team"] == UNITED)]
            pts = int(pts_row["pts"].iloc[0]) if len(pts_row) else None
            real = lambda v: None if pd.isna(v) else float(v) * f  # noqa: E731
            money_rows.append({
                "season": int(r.season), "season_label": season_label(int(r.season)), "fy_end_year": int(r.fy_end_year),
                "revenue": real(r.revenue), "wages": real(r.wages), "wages_to_revenue": opt(r.wages_to_revenue),
                "wages_per_point": None if pts in (None, 0) or pd.isna(r.wages) else real(r.wages) / pts,
                "interest_paid": real(r.interest_paid), "dividends_paid": real(r.dividends_paid),
                "debt_issue_costs": real(r.debt_issue_costs), "net_debt": real(r.net_debt), "borrowings": real(r.borrowings),
            })
        if money_rows:
            totals = {
                "first_fy": money_rows[0]["fy_end_year"], "last_fy": money_rows[-1]["fy_end_year"],
                "interest_paid": sum(m["interest_paid"] or 0 for m in money_rows),
                "dividends_paid": sum(m["dividends_paid"] or 0 for m in money_rows),
                "debt_issue_costs": sum(m["debt_issue_costs"] or 0 for m in money_rows),
                "latest_net_debt": money_rows[-1]["net_debt"],
            }
    out = {
        "generated": TODAY, "cpi_base": d.cpi.attrs.get("latest_label", ""),
        "model": {"resource": resource, "resource_label": label, "intercept": model.intercept, "slope": model.slope,
                  "r2": model.r2, "n": model.n, "first_season": season_label(model.seasons[0]),
                  "last_season": season_label(model.seasons[1])},
        "points": points,
        "club_summary": [{**r._asdict(), "display": display(r.team)} for r in summary.itertuples(index=False)],
        "net_spend": net_rows, "united_money": money_rows, "glazer_totals": totals,
    }
    return out, data


# ---------- transfers ------------------------------------------------------------

def build_transfers(d: Data) -> tuple[dict[str, Any], pd.DataFrame]:
    if d.transfers is None or d.squad is None:
        return {"generated": TODAY, "threshold_gbp_real": transfer_roi.THRESHOLD_GBP, "signings": [], "clubs": BIG_SIX}, pd.DataFrame()
    sig = transfer_roi.signings(d.transfers, BIG_SIX)
    roi = transfer_roi.evaluate(sig, d.transfers, d.squad, d.gps, CURRENT)
    roi["value_rating"] = transfer_roi.value_score(roi)
    roi["season_label"] = roi["season"].map(season_label)
    # Attribute a signing to the United manager in charge on 1 September of that
    # season (end of the summer window). Winter signings are an approximation.
    roi["signed_under"] = [
        d.manager_on(pd.Timestamp(f"{s}-09-01")) if t == UNITED else None for s, t in zip(roi["season"], roi["team"])
    ]
    cards = [card(r) for r in roi.to_dict("records")]
    return {"generated": TODAY, "threshold_gbp_real": transfer_roi.THRESHOLD_GBP, "signings": cards, "clubs": BIG_SIX}, roi


CARD_FIELDS = list(schema.SigningCard.__annotations__)


def card(r: dict[str, Any]) -> dict[str, Any]:
    out = {k: opt(r.get(k)) for k in CARD_FIELDS}
    out["age"] = None if out["age"] is None else int(out["age"])
    for k in ["season", "league_minutes", "starts", "value_rating"]:
        out[k] = int(out[k])
    out["still_at_club"] = bool(r["still_at_club"])
    return out


# ---------- scouting -------------------------------------------------------------

def tenures_for_clustering(d: Data) -> pd.DataFrame:
    rows = []
    ov = d.overview.set_index(["season", "team"]) if d.overview is not None else None
    coaches = d.coaches[d.coaches["team"].isin(COMPARISON)].copy()
    utd = d.united_managers.rename(columns={"manager": "manager"})[["manager", "start", "end"]].copy()
    utd["team"] = UNITED
    spells = pd.concat([coaches[["team", "manager", "start", "end"]], utd], ignore_index=True)
    spells.loc[spells["end"] > pd.Timestamp(TODAY), "end"] = pd.NaT
    for sp in spells.itertuples(index=False):
        log = d.log[d.log["team"] == sp.team]
        games = manager_eras.tenure_games(log, sp.start, sp.end)
        if len(games) < 19:
            continue
        shares = manager_eras.season_share(games, d.gps)
        elo_team = d.elo[d.elo["team"] == sp.team]
        e0, e1 = manager_eras.elo_at(elo_team, sp.start, sp.end)
        seasons_equiv = len(games) / 38
        ns = manager_eras.tenure_net_spend(d.net_spend[d.net_spend["team"] == sp.team], shares)
        ages = [(float(ov.loc[(s, sp.team), "avg_age"]), w) for s, w in shares.items()
                if ov is not None and (s, sp.team) in ov.index and pd.notna(ov.loc[(s, sp.team), "avg_age"])]
        rows.append({
            "team": sp.team, "manager": sp.manager, "start": sp.start, "end": sp.end,
            "ppg": float(games["pts"].mean()),
            "net_spend_per_season": (ns or 0.0) / seasons_equiv,
            "avg_squad_age": sum(a * w for a, w in ages) / sum(w for _, w in ages) if ages else np.nan,
            "elo_change_per_season": ((e1 or 0) - (e0 or 0)) / seasons_equiv,
        })
    return pd.DataFrame(rows).dropna(subset=clustering.FEATURES).reset_index(drop=True)


def series_points(dates: pd.Series, values: pd.Series, step: int = 1) -> list[dict[str, Any]]:
    return [{"date": dd.strftime("%Y-%m-%d"), "v": round(float(v), 3)} for dd, v in list(zip(dates, values))[::step]]


def build_scouting(d: Data) -> tuple[dict[str, Any], pd.DataFrame]:
    # Elo history
    elo_series = []
    if d.clubelo is not None:
        src = "ClubElo (clubelo.com)"
        for team in BIG_SIX:
            t = d.clubelo[d.clubelo["team"] == team]
            t = t[pd.to_datetime(t["start"]) >= "1992-08-01"]
            elo_series.append({"team": team, "display": display(team), "points": series_points(pd.to_datetime(t["start"]), t["elo"], 7)})
    else:
        src = "Computed from PL results (ClubElo API unavailable during build)"
        for team in BIG_SIX:
            t = d.elo[d.elo["team"] == team].sort_values("date")
            elo_series.append({"team": team, "display": display(team), "points": series_points(t["date"], t["elo"], 2)})

    # Change points
    cps = []
    roll = changepoint.rolling_ppg(d.log, UNITED)
    elo_u = d.united_elo
    for label, dates, values in [("ROLLING 19-GAME PPG", roll["date"], roll["rolling_ppg"]), ("ELO RATING", elo_u["date"], elo_u["elo"])]:
        sig = values.to_numpy(dtype=float)
        sens = changepoint.sensitivity(sig)
        strong = [int(b) for b, s in zip(sens["index"], sens["support"]) if s >= 0.5]
        segs = changepoint.segment_means(sig, strong)
        dl = list(dates)
        cps.append({
            "label": label,
            "series": series_points(dates, values, 2),
            "breaks": [{"index": int(b), "date": dl[int(b)].strftime("%Y-%m-%d"), "support": float(s)} for b, s in zip(sens["index"], sens["support"])],
            "segments": [{"start": dl[s].strftime("%Y-%m-%d"), "end": dl[e - 1].strftime("%Y-%m-%d"), "mean": m} for s, e, m in segs],
        })

    # Manager bounce
    coaches = d.coaches.copy()
    coaches.loc[coaches["end"] > pd.Timestamp(TODAY), "end"] = pd.NaT
    others = coaches[coaches["team"] != UNITED]
    league_changes = manager_bounce.manager_changes(others, d.log)
    league_curve = manager_bounce.bounce_curve(manager_bounce.aligned_points(league_changes, d.log))
    utd = d.united_managers[["manager", "start", "end"]].copy()
    utd["team"] = UNITED
    utd_changes = manager_bounce.manager_changes(utd, d.log)
    utd_aligned = manager_bounce.aligned_points(utd_changes, d.log)
    utd_curves = []
    for cid, ch in enumerate(utd_changes.itertuples(index=False)):
        c = manager_bounce.bounce_curve(utd_aligned[utd_aligned["change_id"] == cid])
        utd_curves.append({"manager": ch.manager, "start": ch.start.strftime("%Y-%m-%d"),
                           "curve": [{"rel": int(r.rel), "ppg": float(r.ppg_smooth), "n": int(r.size)} for r in c.itertuples(index=False)]})

    # Clusters
    ten = tenures_for_clustering(d)
    res = clustering.cluster_tenures(ten)
    names = clustering.name_clusters(res.centers_z)
    ten["cluster"] = [names[i] for i in res.labels]
    ten["x"], ten["y"] = res.coords[:, 0], res.coords[:, 1]
    cluster_points = [{
        "team": r.team, "display": display(r.team), "manager": r.manager, "start": r.start.strftime("%Y-%m-%d"),
        "end": None if pd.isna(r.end) else r.end.strftime("%Y-%m-%d"), "x": r.x, "y": r.y, "cluster": r.cluster,
        "ppg": r.ppg, "net_spend_per_season": r.net_spend_per_season, "avg_squad_age": r.avg_squad_age,
        "elo_change_per_season": r.elo_change_per_season,
    } for r in ten.itertuples(index=False)]

    # Regression to the mean
    rtm = clustering.regression_to_mean(d.table[d.table["season"] < CURRENT])
    league = rtm[rtm["team"] != UNITED]
    united = rtm[rtm["team"] == UNITED]
    out = {
        "generated": TODAY, "elo": elo_series, "elo_source": src, "changepoints": cps,
        "penalties": [float(p) for p in changepoint.PENALTIES],
        "bounce_league": [{"rel": int(r.rel), "ppg": float(r.ppg_smooth), "n": int(r.size)} for r in league_curve.itertuples(index=False)],
        "bounce_united": utd_curves, "bounce_n_changes": int(len(league_changes)),
        "clusters": cluster_points, "cluster_k": res.k, "silhouettes": {str(k): v for k, v in res.silhouettes.items()},
        "pca_explained": res.explained,
        "rtm_points": [{"team": r.team, "season": int(r.season), "deviation": r.deviation, "next_change": r.next_change} for r in rtm.itertuples(index=False)],
        "rtm_league_slope": clustering.slope(league["deviation"], league["next_change"]),
        "rtm_united_slope": clustering.slope(united["deviation"], united["next_change"]),
    }
    return out, ten


# ---------- managers -------------------------------------------------------------

def person_slug(slug: str) -> str:
    for suffix in ["-caretaker", "-interim", "-2021"]:
        slug = slug.replace(suffix, "")
    return slug


def starters_with_dates(d: Data) -> pd.DataFrame | None:
    if d.starters is None or d.tm_fixtures is None:
        return None
    fx = d.tm_fixtures.copy()
    fx["date"] = pd.to_datetime(fx["date"], dayfirst=True)
    st = d.starters.merge(fx[["report_id", "date"]], on="report_id", how="left")
    st["name"] = st["player_slug"].map(name_from_slug)
    return st


PARTICLES = {"van", "der", "de", "den", "da", "dos", "di", "le", "la", "von", "ten"}


def name_from_slug(slug: str) -> str:
    """'edwin-van-der-sar' -> 'Edwin van der Sar'. Transfermarkt slugs sometimes
    carry an encoded left-to-right mark ('-lrm') which we drop."""
    words = [w for w in slug.split("-") if w and w not in {"lrm", "rlm"}]
    return " ".join(w if (i > 0 and w in PARTICLES) else w.capitalize() for i, w in enumerate(words))


def lineup_block(st: pd.DataFrame, label: str, league_games: int) -> dict[str, Any] | None:
    xi = manager_eras.common_xi(st)
    if xi is None:
        return None
    return {"label": label, **xi, "league_games": league_games,
            "coverage": manager_eras.coverage(int(xi["matches_with_lineup"]), league_games)}


def build_managers(d: Data, fin_data: pd.DataFrame, roi: pd.DataFrame, ten: pd.DataFrame) -> dict[str, Any]:
    st_all = starters_with_dates(d)
    utd_model = fin_data[fin_data["team"] == UNITED].set_index("season")
    credit_by_slug = {c["slug"]: c for c in d.credits}
    out = []
    for m in d.united_managers.itertuples(index=False):
        end = None if pd.isna(m.end) else m.end
        games = manager_eras.tenure_games(d.united_log, m.start, end)
        rec = manager_eras.record(games)
        shares = manager_eras.season_share(games, d.gps)
        in_charge = manager_eras.seasons_in_charge(games, d.gps)
        finished = [s for s in in_charge if s < CURRENT]
        tab = d.table[(d.table["team"] == UNITED) & (d.table["season"].isin(finished))]
        best = tab.sort_values("position").head(1)
        trophies = d.trophies[(d.trophies["date"] >= m.start) & ((end is None) | (d.trophies["date"] < (end or pd.Timestamp.max)))]
        e0, e1 = manager_eras.elo_at(d.united_elo, m.start, end)
        ns = manager_eras.tenure_net_spend(d.net_spend[d.net_spend["team"] == UNITED], shares)

        # A season counts towards a manager's model score only if they managed at least
        # a quarter of it: one game at the end of a season isn't that manager's season.
        model_rows = [(utd_model.loc[s, "places_vs_model"], w) for s, w in shares.items()
                      if s in utd_model.index and s < CURRENT and w >= 0.25]
        pvm = sum(v * w for v, w in model_rows) / sum(w for _, w in model_rows) if model_rows else None

        first, rest = manager_bounce.bounce_stat(games["pts"].to_numpy())
        clus = ten[(ten["team"] == UNITED) & (ten["start"] == m.start)]
        cluster = None if clus.empty else str(clus["cluster"].iloc[0])

        lineup = None
        season_lineups: list[dict[str, Any]] = []
        if st_all is not None:
            st = st_all[(st_all["date"] >= m.start) & ((end is None) | (st_all["date"] < (end or pd.Timestamp.max)))]
            lineup = lineup_block(st, "Whole tenure", rec["games"])
            for s, g in games.groupby("season"):
                blk = lineup_block(st[st["season"] == s], season_label(int(s)), len(g))
                if blk is not None:
                    season_lineups.append(blk)

        mine = roi[(roi["team"] == UNITED) & (roi["signed_under"] == m.slug)] if not roi.empty else pd.DataFrame()
        mature = mine[mine["season"] < CURRENT] if not mine.empty else mine
        best_s = mature.dropna(subset=["cost_per_1000_min"]).sort_values("cost_per_1000_min").head(2) if not mine.empty else mine
        worst_s = mature.sort_values("cost_per_1000_min", ascending=False, na_position="first").head(2) if not mine.empty else mine
        worst_s = worst_s[~worst_s["player_id"].isin(best_s["player_id"])] if not mine.empty else worst_s

        n_league = int((trophies["competition"] == "Premier League").sum())
        parts = []
        if n_league:
            parts.append(f"{n_league} LEAGUE TITLE{'S' if n_league > 1 else ''}")
        if ns is not None and rec["games"] >= 19:
            parts.append(f"{money(ns)} NET SPEND")
        if pvm is not None and rec["games"] >= 19:
            parts.append(f"{pvm:+.1f} PLACES VS SQUAD-VALUE MODEL")
        if not parts and rec["ppg"] is not None:
            parts.append(f"{rec['ppg']:.2f} POINTS PER GAME IN {rec['games']} GAMES")
        tagline = " · ".join(parts)

        ps = person_slug(m.slug)
        credit = credit_by_slug.get(ps)
        out.append({
            "slug": m.slug, "name": m.manager, "interim": bool(m.interim),
            "start": m.start.strftime("%Y-%m-%d"), "end": None if end is None else end.strftime("%Y-%m-%d"),
            **rec, "xg_diff_pg": None,
            "best_finish": None if best.empty else int(best["position"].iloc[0]),
            "best_finish_season": None if best.empty else season_label(int(best["season"].iloc[0])),
            "trophies": [{"date": t.date.strftime("%Y-%m-%d"), "competition": t.competition, "season": t.season} for t in trophies.itertuples(index=False)],
            "elo_start": e0, "elo_end": e1, "net_spend_real": ns, "places_vs_model": pvm, "model_seasons": len(model_rows),
            "how_it_ended": m.how_it_ended, "tagline": tagline,
            "bounce_first10_ppg": first, "bounce_rest_ppg": rest, "cluster": cluster,
            "lineup": lineup, "season_lineups": season_lineups,
            "best_signings": [card(r) for r in best_s.to_dict("records")] if not mine.empty else [],
            "worst_signings": [card(r) for r in worst_s.to_dict("records")] if not mine.empty else [],
            "timeline": manager_eras.ppg_timeline(games),
            "ratings": {
                "win_pct": manager_eras.rating(rec["win_pct"], 0.2, 0.8),
                "ppg": manager_eras.rating(rec["ppg"], 0.8, 2.5),
                "attack": manager_eras.rating(rec["gf_pg"], 0.8, 2.6),
                "defence": manager_eras.rating(None if rec["ga_pg"] is None else -rec["ga_pg"], -1.6, -0.6),
                "elo": manager_eras.rating(e1, 1550, 1900),
                "value": manager_eras.rating(pvm, -4, 4),
            },
            "portrait": None if credit is None else credit["file"],
            "credit": None if credit is None else {k: credit[k] for k in ["slug", "name", "title", "author", "license", "source_url"]},
        })
    note = ("Line-ups come from Transfermarkt match reports (league games only). Coverage shows the share of league "
            "games in the tenure with a recorded XI. Older reports list players by position group only: there the "
            "formation is inferred from the group counts and left-to-right positions are approximate.")
    return {"generated": TODAY, "managers": out, "lineup_note": note}


# ---------- menu -----------------------------------------------------------------

def build_menu(d: Data, managers: dict[str, Any], fin: dict[str, Any], fin_data: pd.DataFrame, sim: dict[str, Any], roi: pd.DataFrame) -> dict[str, Any]:
    heads: list[str] = []
    tips: list[str] = []
    u = fin_data[(fin_data["team"] == UNITED) & (fin_data["season"] < CURRENT)]
    post = u[u["season"] >= 2013]
    if len(post):
        below = int((post["places_vs_model"] < 0).sum())
        heads.append(f"UNITED HAVE FINISHED BELOW THE SQUAD-VALUE MODEL IN {below} OF {len(post)} SEASONS SINCE FERGUSON")
        worst = post.sort_values("places_vs_model").iloc[0]
        heads.append(f"WORST SEASON VS MONEY: {season_label(int(worst['season']))}, {abs(worst['places_vs_model']):.1f} PLACES BELOW THE MODEL")
    ferg = d.united_log[d.united_log["date"] < pd.Timestamp("2013-07-01")]["pts"].mean()
    after = d.united_log[d.united_log["date"] >= pd.Timestamp("2013-07-01")]["pts"].mean()
    heads.append(f"POINTS PER GAME: {ferg:.2f} UNDER FERGUSON (PL ERA), {after:.2f} SINCE")
    ns_post = d.net_spend[(d.net_spend["team"] == UNITED) & (d.net_spend["season"] >= 2013)]["net_spend"].sum()
    heads.append(f"{money(ns_post)} NET TRANSFER SPEND SINCE 2013-14 (TODAY'S MONEY, KNOWN FEES)")
    gt = fin.get("glazer_totals")
    if gt:
        heads.append(f"{money(gt['interest_paid'] + gt['dividends_paid'])} PAID OUT IN INTEREST AND DIVIDENDS, FY{gt['first_fy']}-FY{gt['last_fy']}")
    cur = next((s for s in sim["seasons"] if s["season"] == CURRENT), None)
    if cur:
        t = next((x for x in cur["teams"] if x["team"] == UNITED), None)
        if t:
            heads.append(f"{cur['label']} SIMULATION: {t['p_title'] * 100:.1f}% TITLE CHANCE, {t['p_top4'] * 100:.0f}% TOP-FOUR CHANCE")
    if not roi.empty:
        u_roi = roi[(roi["team"] == UNITED) & (roi["season"] < CURRENT) & roi["cost_per_1000_min"].notna()]
        if len(u_roi):
            w = u_roi.sort_values("cost_per_1000_min", ascending=False).iloc[0]
            heads.append(f"WORST VALUE SIGNING: {w['player'].upper()}, {money(w['cost_per_1000_min'])} PER 1,000 LEAGUE MINUTES")
    seasons_luck = [s for s in sim["seasons"] if not s["in_progress"]]
    lucky = []
    for s in seasons_luck:
        t = next((x for x in s["teams"] if x["team"] == UNITED), None)
        if t and t["actual_points"] is not None:
            lucky.append((t["actual_points"] - t["p50"], s["label"]))
    if lucky:
        lo = min(lucky)
        tips.append(f"United's unluckiest season by simulation was {lo[1]}: {abs(lo[0]):.0f} points below their median simulated total.")
        hi = max(lucky)
        tips.append(f"United's luckiest season by simulation was {hi[1]}: {hi[0]:.0f} points above their median simulated total.")
    ms = [m for m in managers["managers"] if m["games"] >= 19 and not m["interim"]]
    if ms:
        best = max(ms, key=lambda m: m["ppg"] or 0)
        tips.append(f"Highest PPG of any permanent United manager in the PL era: {best['name']} ({best['ppg']:.2f}).")
    tips.append(f"The squad-value model explains {fin['model']['r2'] * 100:.0f}% of the variation in points per game across all PL clubs since {fin['model']['first_season']}.")
    if fin["club_summary"]:
        worst_club = fin["club_summary"][0]
        tips.append(f"Of the big six, {worst_club['display']} have the worst average return on squad value: {worst_club['mean_residual_ppg']:+.2f} PPG against the model.")
    hero = f"{post['places_vs_model'].mean():+.1f}" if len(post) else "NO DATA"
    return {"generated": TODAY, "current_season_label": season_label(CURRENT), "headlines": heads, "tips": tips, "hero_stat": hero}


# ---------- methodology + gaps ---------------------------------------------------

def sources(d: Data) -> list[dict[str, Any]]:
    lineup_ok = d.starters is not None
    return [
        {"name": "football-data.co.uk", "url": "https://www.football-data.co.uk/englandm.php", "used_for": "Match results and bookmaker odds", "coverage": "1993-94 to present", "status": "ok"},
        {"name": "engsoccerdata (J. Curley)", "url": "https://github.com/jalapic/engsoccerdata", "used_for": "1992-93 results; 1985-92 First Division results to warm up Elo", "coverage": "1985-86 to 1992-93", "status": "ok"},
        {"name": "Transfermarkt", "url": "https://www.transfermarkt.co.uk", "used_for": "Squad values and ages, transfers and fees, coach histories, player league minutes, line-ups and formations", "coverage": "Values from 2004-05; other data full era", "status": "ok" if lineup_ok else "partial"},
        {"name": "SEC EDGAR (Manchester United plc 20-F XBRL)", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001549107", "used_for": "Revenue, wages, interest, dividends, net debt", "coverage": "FY2016 to FY2025", "status": "partial"},
        {"name": "ONS CPI index (D7BT)", "url": "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23", "used_for": "Inflation adjustment", "coverage": "1988 to latest month", "status": "ok"},
        {"name": "ECB reference rates", "url": "https://data.ecb.europa.eu/", "used_for": "EUR to GBP conversion of Transfermarkt figures", "coverage": "1999 to present", "status": "ok"},
        {"name": "ClubElo", "url": "http://clubelo.com", "used_for": "Elo ratings", "coverage": "API unreachable (HTTP 502) during build", "status": "ok" if d.clubelo is not None else "unavailable"},
        {"name": "Understat / FBref", "url": "https://understat.com", "used_for": "xG (planned)", "coverage": "Understat disallows crawling in robots.txt; FBref returns HTTP 403", "status": "unavailable"},
        {"name": "Wikimedia Commons", "url": "https://commons.wikimedia.org", "used_for": "Freely licensed manager portraits", "coverage": f"{len(d.credits)} of 12 managers", "status": "ok" if len(d.credits) == 12 else "partial"},
    ]


MODEL_NOTES = [
    ("Squad-value model", "PPG = a + b·log(club squad value ÷ league average), fitted by OLS on every PL club-season since 2004-05. A residual is actual PPG minus predicted; it is converted to league places using that season's own table. Squad market value stands in for wages because no open wage-bill data covers every club."),
    ("Dixon-Coles", "Per-season attack and defence strengths, home advantage and a low-score correction (rho), fitted by maximum likelihood with an analytic gradient and a sum-to-zero constraint on log-attack. Finished seasons weight every game equally; the season in progress also uses the previous season, down-weighted by exponential time decay (xi = 0.0019/day)."),
    ("Monte Carlo", "10,000 seeded simulations per season. Finished seasons replay every fixture; the current season keeps real results and simulates the rest. Reports points percentiles, title, top-four and relegation probabilities, and a convergence check."),
    ("Market expected points", "Expected points implied by average bookmaker odds (normalised to remove the margin). Used in place of xG-based expected points, which needed data we could not source."),
    ("Elo", "Standard football Elo (K=20, home advantage 65, goal-margin multiplier), computed from league results and warmed up on 1985-92 First Division games. PL games only."),
    ("Change points", "PELT (ruptures, L2 cost) on United's rolling 19-game PPG and Elo, run at seven penalties. A break counts as real only if it appears at half or more of the penalties."),
    ("Manager bounce", "Every PL managerial spell of 10+ league games, aligned at the new manager's first game; mean points per game from -10 to +40, smoothed over 5 games. United's spells are compared with every other club's."),
    ("Tenure clusters", "Big-six tenures of 19+ league games described by PPG, net spend per season, squad age and Elo change per season; standardised, k-means with k chosen by silhouette score, PCA for the 2D view."),
    ("Transfer ROI", "Big-six signings over £10m in today's money: league minutes, starts, goals plus assists per 90, resale fee and net cost per 1,000 league minutes."),
]

ASSUMPTIONS = [
    "All money is in pounds at the latest UK CPI price level. Euro figures from Transfermarkt use the ECB annual average rate for the season's start year; the 1999 rate is used before the euro existed.",
    "Seasons run from July to June. United's financial year ends on 30 June and maps to the season ending in it.",
    "Points per game everywhere: 1992-95 seasons had 42 games.",
    "Only known transfer fees count. Unknown fees are excluded, not treated as free transfers. Loans are excluded.",
    "A season's net spend is split between managers in proportion to the league games each managed that season.",
    "Signings are credited to the United manager in charge on 1 September of the signing season.",
    "League games only for manager records, line-ups and minutes.",
]


def write_gaps(d: Data, managers: dict[str, Any]) -> str:
    cov_lines = []
    for m in managers["managers"]:
        lu = m["lineup"]
        cov = "no line-ups" if lu is None else f"{lu['matches_with_lineup']}/{m['games']} league games ({(lu['coverage'] or 0) * 100:.0f}%)"
        cov_lines.append(f"| {m['name']}{' (interim)' if m['interim'] else ''} | {cov} |")
    missing_portraits = [m["name"] for m in managers["managers"] if m["portrait"] is None]
    missing_portraits = sorted(set(missing_portraits))
    fin_years = "none" if d.fin is None else f"FY{int(d.fin.dropna(subset=['revenue'])['fy_end_year'].min())}-FY{int(d.fin.dropna(subset=['revenue'])['fy_end_year'].max())}"
    text = f"""# DATA GAPS

Generated by `analysis/export.py` on {TODAY}. Nothing listed here was estimated
or invented: missing values are `null` in the JSON and show as **NO DATA** on the site.

## Unavailable sources

- **xG and shots (Understat, FBref).** Understat's robots.txt disallows all crawlers and FBref
  returned HTTP 403, so there is no xG. Affected: xG difference per manager (null),
  xG-based expected points (replaced by *bookmaker-odds* expected points, clearly labelled),
  and the xG feature in tenure clustering (dropped).
- **ClubElo API.** HTTP 502 on every attempt. Elo is computed from league results instead
  (`models/elo.py`). It covers PL games only, not cups or Europe.

## Financial data

- **Wage bills for every PL club.** No open dataset exists (Deloitte, Capology and Statista
  are paywalled). The spending model uses Transfermarkt **squad market value** as the resource
  measure (2004-05 onward). To fit the true wage model, add `analysis/data/manual/club_wages.csv`
  (`season,team,wages_gbp`) from published accounts; the pipeline picks it up automatically.
- **Squad market values before 2004-05.** Transfermarkt has none, so the model covers 2004-05 onward.
- **United financials before FY2016.** SEC XBRL data starts with the FY2018 20-F, which restates
  FY2016-17. Available: {fin_years}. Earlier 20-F filings (FY2012-15) are HTML/PDF only and
  were not hand-transcribed. Glazer-era outflows from 2005 to 2015 are therefore missing, so the
  site's outflow totals cover the filed years only.
- **Rival clubs' wages-to-revenue and cost per point.** Not available (same reason as wages).
  Rival comparisons use squad value and net transfer spend instead.
- **Debt issue costs** appear in XBRL for only some years. Other years are null, not zero.

## Transfers

- Transfermarkt fees are reported figures and may exclude add-ons. Unknown fees ({'see JSON' if d.transfers is None else f"{(d.transfers['fee_eur'].isna() & ~d.transfers['is_loan']).mean() * 100:.0f}% of non-loan moves"}) are excluded.
- Pre-1999 euro figures are converted at the 1999 ECB rate.
- No transfer dates on season pages, so summer and winter windows cannot be separated when
  crediting spend to managers (proportional split used instead).

## Line-up coverage (United league games with a recorded XI)

| Manager | Coverage |
|---|---|
{chr(10).join(cov_lines)}

## Manager portraits

Free-licence portraits found for {len(d.credits)} of 12 people. Initials fallback used for:
{', '.join(missing_portraits) if missing_portraits else 'none'}.

## Other limitations

- Older Transfermarkt match reports (mostly before 2002) list starters by position group, not on a
  pitch. For those games the formation is *inferred* from the group counts (e.g. 4 defenders,
  4 midfielders, 2 forwards = 4-4-2) and left-to-right positions are approximate. The site flags
  this as "INFERRED".
- Elo ratings for 1992-93 depend on the 1985-92 warm-up period.
- Trophy dates for league titles are approximate. They are only used to attribute each
  trophy to a manager.
- Interim flags are hand-checked for United only. For rivals, short spells are simply
  filtered out (fewer than 10 or 19 league games, depending on the model).
- The bounce baseline needs 10 PL games before a change. For a newly promoted club these
  can come from an earlier PL spell.
"""
    GAPS_FILE.write_text(text)
    return text


def build_methodology(d: Data, gaps: str) -> dict[str, Any]:
    credits = [{k: c[k] for k in ["slug", "name", "title", "author", "license", "source_url"]} for c in d.credits]
    return {
        "generated": TODAY, "sources": sources(d),
        "models": [{"name": n, "summary": s} for n, s in MODEL_NOTES],
        "assumptions": ASSUMPTIONS, "gaps_markdown": gaps, "credits": credits,
    }


# ---------- main -----------------------------------------------------------------

def write(name: str, obj: dict[str, Any]) -> None:
    data = clean(obj)
    schema.validate(data, schema.EXPORTS[name])
    text = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    size = len(text.encode())
    flag = "" if size <= MAX_BYTES else "  <-- OVER 300 KB BUDGET"
    (WEB_DATA / name).write_text(text)
    print(f"[export] {name}: {size / 1000:.0f} KB{flag}")


def main() -> None:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    d = Data()
    sim, _ = build_simulate(d)
    fin, fin_data = build_finances(d)
    transfers, roi = build_transfers(d)
    scouting, ten = build_scouting(d)
    managers = build_managers(d, fin_data, roi, ten)
    menu = build_menu(d, managers, fin, fin_data, sim, roi)
    gaps = write_gaps(d, managers)
    meth = build_methodology(d, gaps)
    for name, obj in [("menu.json", menu), ("managers.json", managers), ("finances.json", fin), ("simulate.json", sim),
                      ("scouting.json", scouting), ("transfers.json", transfers), ("methodology.json", meth),
                      ("sources.json", {"generated": TODAY, "sources": meth["sources"]})]:
        write(name, obj)
    WEB_TYPES.write_text(schema.typescript_definitions())
    print(f"[export] wrote {WEB_TYPES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
