"""Elo ratings computed from Premier League results.

Why our own Elo: the ClubElo API was unreachable (HTTP 502) during the build.
This is the standard football Elo (as used by eloratings.net):
  * expected score  E = 1 / (1 + 10^((R_opp - R_team - H) / 400))
  * update          R += K * G * (S - E), where G grows with goal margin
  * H = home advantage in rating points.
Clubs entering the PL take the average rating of the clubs that left, so the
league's total rating is conserved. It only sees PL games, unlike ClubElo.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EloParams:
    k: float = 20.0
    home_adv: float = 65.0
    start: float = 1500.0


def margin_multiplier(goal_diff: int) -> float:
    gd = abs(goal_diff)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8


def expected_score(r_team: float, r_opp: float, home_adv: float) -> float:
    return 1.0 / (1.0 + 10 ** ((r_opp - r_team - home_adv) / 400))


def run_elo(results: pd.DataFrame, params: EloParams = EloParams()) -> pd.DataFrame:
    """Return one row per team per match with the rating *after* the match."""
    ratings: dict[str, float] = {}
    rows: list[dict[str, object]] = []
    results = results.sort_values(["date", "home"]).reset_index(drop=True)
    prev_season_teams: set[str] = set()
    for season, games in results.groupby("season", sort=True):
        teams = set(games["home"]) | set(games["away"])
        leavers = prev_season_teams - teams
        entrants = teams - prev_season_teams
        if prev_season_teams:
            entry = float(np.mean([ratings[t] for t in leavers])) if leavers else params.start
            for t in entrants:
                ratings[t] = entry
        else:
            for t in teams:
                ratings[t] = params.start
        for g in games.itertuples(index=False):
            rh, ra = ratings[g.home], ratings[g.away]
            eh = expected_score(rh, ra, params.home_adv)
            sh = 1.0 if g.hg > g.ag else 0.5 if g.hg == g.ag else 0.0
            delta = params.k * margin_multiplier(int(g.hg - g.ag)) * (sh - eh)
            ratings[g.home] = rh + delta
            ratings[g.away] = ra - delta
            rows.append({"season": season, "date": g.date, "team": g.home, "elo": ratings[g.home], "elo_before": rh})
            rows.append({"season": season, "date": g.date, "team": g.away, "elo": ratings[g.away], "elo_before": ra})
        prev_season_teams = teams
    return pd.DataFrame(rows)


def season_end_elo(elo: pd.DataFrame) -> pd.DataFrame:
    return elo.sort_values("date").groupby(["season", "team"]).tail(1)[["season", "team", "elo"]]
