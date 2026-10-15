"""Transfer return on investment for big-six signings over £10m (real).

For each signing we follow the player's league career *at that club*:
league minutes, starts, goals + assists per 90, seasons as a regular starter,
and the fee recouped if the player was later sold. The headline efficiency number is
net cost (fee minus resale) per 1,000 league minutes: what each chunk of
actual pitch time cost.

Limitations (also in DATA_GAPS.md): Transfermarkt fees are reported figures
that may exclude add-ons; unknown fees are dropped, never treated as free;
only league minutes count (cups and Europe excluded).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

THRESHOLD_GBP = 10_000_000
REGULAR_SHARE = 0.5  # a "regular starter" season = at least half the available league minutes


def signings(transfers: pd.DataFrame, clubs: list[str], threshold: float = THRESHOLD_GBP) -> pd.DataFrame:
    t = transfers[(transfers["direction"] == "in") & (~transfers["is_loan"]) & transfers["team"].isin(clubs)]
    t = t.dropna(subset=["fee_gbp_real"])
    return t[t["fee_gbp_real"] >= threshold].copy()


def departure(transfers: pd.DataFrame, team: str, player_id: str, after_season: int) -> pd.Series | None:
    """The first transfer *out* of the club for this player after signing.
    Loans out are skipped because the player usually came back."""
    outs = transfers[(transfers["team"] == team) & (transfers["player_id"] == player_id)
                     & (transfers["direction"] == "out") & (transfers["season"] >= after_season) & (~transfers["is_loan"])]
    outs = outs[~((outs["season"] == after_season) & outs["fee_text"].str.contains("End of loan", case=False, na=False))]
    if outs.empty:
        return None
    return outs.sort_values("season").iloc[0]


def season_minutes_available(games: int) -> int:
    return games * 90


def evaluate(signing_rows: pd.DataFrame, transfers: pd.DataFrame, squad_stats: pd.DataFrame,
             games_per_season: dict[int, int], current_season: int) -> pd.DataFrame:
    rows = []
    for s in signing_rows.itertuples(index=False):
        dep = departure(transfers, s.team, s.player_id, s.season)
        last_season = int(dep["season"]) if dep is not None else current_season
        stats = squad_stats[(squad_stats["team"] == s.team) & (squad_stats["player_id"] == s.player_id)
                            & (squad_stats["season"] >= s.season) & (squad_stats["season"] <= last_season)]
        minutes = int(stats["minutes"].sum())
        starts = int((stats["apps"] - stats["subs_on"]).clip(lower=0).sum())
        ga = int(stats["goals"].sum() + stats["assists"].sum())
        seasons_played = stats[stats["minutes"] > 0]
        regular = sum(
            1 for r in stats.itertuples(index=False)
            if r.minutes >= REGULAR_SHARE * season_minutes_available(games_per_season.get(int(r.season), 38))
        )
        n_seasons = max(1, last_season - s.season + (0 if dep is not None else 1))
        sale = None if dep is None else (dep["fee_gbp_real"] if pd.notna(dep["fee_gbp_real"]) else None)
        net_cost = s.fee_gbp_real - (sale or 0.0)
        rows.append({
            "team": s.team, "player": s.player, "player_id": s.player_id, "season": int(s.season),
            "age": s.age, "position": s.position, "from_club": s.other_club,
            "fee_gbp_real": float(s.fee_gbp_real),
            "league_minutes": minutes, "starts": starts,
            "ga_per90": (ga / minutes * 90) if minutes >= 450 else None,
            "years_at_club": float(n_seasons),
            "sale_fee_gbp_real": None if sale is None else float(sale),
            "still_at_club": dep is None,
            "left_season": None if dep is None else int(dep["season"]),
            "net_cost_gbp_real": float(net_cost),
            "cost_per_1000_min": float(net_cost / (minutes / 1000)) if minutes > 0 else None,
            "regular_share": regular / n_seasons,
            "seasons_with_minutes": int(len(seasons_played)),
        })
    out = pd.DataFrame(rows)
    out["value_rank_in_club"] = out.groupby("team")["cost_per_1000_min"].rank(method="first", na_option="bottom")
    return out


def value_score(df: pd.DataFrame) -> pd.Series:
    """0-99 'value rating' for cards: percentile of (lower) cost per 1,000 minutes
    across all evaluated signings. Players with no minutes score 0."""
    c = df["cost_per_1000_min"]
    pct = 1 - c.rank(pct=True)
    return (pct.fillna(0) * 99).round().astype(int)


def best_and_worst(df: pd.DataFrame, n: int = 3, min_seasons_done: int = 1) -> dict[str, dict[str, list[dict[str, object]]]]:
    """Per club: best and worst value. Signings from the current/last season are
    excluded from 'worst' since they haven't had time to play."""
    out: dict[str, dict[str, list[dict[str, object]]]] = {}
    latest = int(df["season"].max())
    for team, g in df.groupby("team"):
        mature = g[g["season"] <= latest - min_seasons_done]
        best = mature.dropna(subset=["cost_per_1000_min"]).sort_values("cost_per_1000_min").head(n)
        worst = mature.sort_values("cost_per_1000_min", ascending=False, na_position="first").head(n)
        out[str(team)] = {
            "best": best.replace({np.nan: None}).to_dict("records"),
            "worst": worst.replace({np.nan: None}).to_dict("records"),
        }
    return out
