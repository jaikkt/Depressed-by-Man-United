"""League tables and per-team match logs built from results."""
from __future__ import annotations

import numpy as np
import pandas as pd


def team_match_log(results: pd.DataFrame) -> pd.DataFrame:
    """One row per team per match (two per fixture), the shape most models want."""
    home = pd.DataFrame({
        "season": results["season"], "date": results["date"], "team": results["home"], "opp": results["away"],
        "venue": "H", "gf": results["hg"], "ga": results["ag"],
    })
    away = pd.DataFrame({
        "season": results["season"], "date": results["date"], "team": results["away"], "opp": results["home"],
        "venue": "A", "gf": results["ag"], "ga": results["hg"],
    })
    log = pd.concat([home, away], ignore_index=True)
    log["pts"] = np.select([log["gf"] > log["ga"], log["gf"] == log["ga"]], [3, 1], 0)
    log["result"] = np.select([log["gf"] > log["ga"], log["gf"] == log["ga"]], ["W", "D"], "L")
    return log.sort_values(["team", "date"]).reset_index(drop=True)


def league_table(results: pd.DataFrame) -> pd.DataFrame:
    """Final (or current) table per season, sorted the PL way: points, GD, GF.
    Points per game is included because 1992-95 seasons had 42 games."""
    log = team_match_log(results)
    t = log.groupby(["season", "team"]).agg(
        played=("pts", "size"), w=("result", lambda s: (s == "W").sum()), d=("result", lambda s: (s == "D").sum()),
        l=("result", lambda s: (s == "L").sum()), gf=("gf", "sum"), ga=("ga", "sum"), pts=("pts", "sum"),
    ).reset_index()
    t["gd"] = t["gf"] - t["ga"]
    t["ppg"] = t["pts"] / t["played"]
    t = t.sort_values(["season", "pts", "gd", "gf"], ascending=[True, False, False, False])
    t["position"] = t.groupby("season").cumcount() + 1
    t["n_teams"] = t.groupby("season")["team"].transform("size")
    return t.reset_index(drop=True)


def ppg_to_position(ppg: float, season_table: pd.DataFrame) -> float:
    """Translate a PPG into the (fractional) league position it would have earned
    that season, by interpolating the season's own PPG-by-position curve."""
    s = season_table.sort_values("position")
    xs = s["ppg"].to_numpy()[::-1]  # ascending PPG
    ys = s["position"].to_numpy()[::-1].astype(float)
    return float(np.interp(ppg, xs, ys))
