"""New-manager bounce: does form jump after a change, and is it real?

Every managerial change in the PL era is aligned so the new manager's first
league game is 0. We take that club's league points from game -10 to +40 and
average across changes. The league-wide baseline uses every *other* club's
changes, so United's bounces are judged against the normal pattern (which,
famously, is mostly regression to the mean: clubs sack managers at a low point).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW = (-10, 40)
MIN_GAMES = 10  # ignore spells shorter than this (mostly one-game caretakers)


def manager_changes(coaches: pd.DataFrame, match_log: pd.DataFrame, min_games: int = MIN_GAMES) -> pd.DataFrame:
    """First PL game index of each manager spell lasting >= min_games league games."""
    rows = []
    for team, games in match_log.groupby("team"):
        games = games.sort_values("date").reset_index(drop=True)
        spells = coaches[coaches["team"] == team]
        for sp in spells.itertuples(index=False):
            end = sp.end if pd.notna(sp.end) else pd.Timestamp.max
            mask = (games["date"] >= sp.start) & (games["date"] < end)
            idx = np.flatnonzero(mask.to_numpy())
            if len(idx) < min_games or idx[0] < abs(WINDOW[0]):
                # need 10 PL games of "before" at the club (for a promoted club these may
                # come from an earlier PL spell; accepted and documented as a limitation)
                continue
            rows.append({"team": team, "manager": sp.manager, "start": sp.start, "first_idx": int(idx[0]), "n_games": len(idx)})
    return pd.DataFrame(rows)


def aligned_points(changes: pd.DataFrame, match_log: pd.DataFrame) -> pd.DataFrame:
    """Long table: change id, relative game, points (NaN when outside data)."""
    logs = {t: g.sort_values("date").reset_index(drop=True) for t, g in match_log.groupby("team")}
    rows = []
    for cid, ch in enumerate(changes.itertuples(index=False)):
        pts = logs[ch.team]["pts"].to_numpy()
        for rel in range(WINDOW[0], WINDOW[1] + 1):
            i = ch.first_idx + rel
            if 0 <= i < len(pts):
                rows.append({"change_id": cid, "team": ch.team, "manager": ch.manager, "rel": rel, "pts": float(pts[i])})
    return pd.DataFrame(rows)


def bounce_curve(aligned: pd.DataFrame, smooth: int = 5) -> pd.DataFrame:
    """Mean points per game by relative game, smoothed with a centred rolling mean."""
    curve = aligned.groupby("rel")["pts"].agg(["mean", "size"]).reset_index()
    curve["ppg_smooth"] = curve["mean"].rolling(smooth, center=True, min_periods=1).mean()
    return curve


def bounce_stat(points_in_spell: np.ndarray, first_n: int = 10) -> tuple[float | None, float | None]:
    """PPG over the first n league games vs the rest of the spell."""
    if len(points_in_spell) == 0:
        return None, None
    first = float(np.mean(points_in_spell[:first_n]))
    rest = float(np.mean(points_in_spell[first_n:])) if len(points_in_spell) > first_n else None
    return first, rest
