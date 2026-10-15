"""Per-manager stats for every United manager of the Premier League era.

League games only throughout (cup games would mix competitions with very
different opposition). Interim/caretaker spells are kept and flagged.

Line-ups: Transfermarkt draws each starting XI on a pitch template, and every
formation uses the same fixed coordinates for each position. So a "slot" is
an exact (top, left) coordinate within a formation, and "most common XI" =
for each slot of the most-used formation, the player with most starts there.
A greedy pass stops one player filling two slots (e.g. a centre-back who
played both left and right of the pair).
"""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd


def label_position(top: float, left: float, back_three: bool = False) -> str:
    """Human label from pitch coordinates (top: 0 = attack end, 80 = own goal).
    In a back three the wide defenders are centre-backs, not full-backs."""
    centre = left + 5  # coordinates are the box's left edge; ~5% to its centre
    side = "L" if centre < 30 else "R" if centre > 60 else "C"
    if top >= 75:
        return "GK"
    if top >= 55:
        return "CB" if back_three else {"L": "LB", "R": "RB", "C": "CB"}[side]
    if top >= 45:
        return {"L": "LWB", "R": "RWB", "C": "DM"}[side]
    if top >= 32:
        return {"L": "LM", "R": "RM", "C": "CM"}[side]
    if top >= 12:
        return {"L": "LW", "R": "RW", "C": "AM"}[side]
    return "ST"


def tenure_games(log: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp | None) -> pd.DataFrame:
    stop = end if end is not None and not pd.isna(end) else pd.Timestamp.max
    return log[(log["date"] >= start) & (log["date"] < stop)].sort_values("date")


def record(games: pd.DataFrame) -> dict[str, float | int | None]:
    n = len(games)
    if n == 0:
        return {"games": 0, "w": 0, "d": 0, "l": 0, "win_pct": None, "ppg": None, "gf_pg": None, "ga_pg": None}
    w = int((games["result"] == "W").sum())
    d = int((games["result"] == "D").sum())
    return {
        "games": n, "w": w, "d": d, "l": n - w - d,
        "win_pct": w / n, "ppg": float(games["pts"].mean()),
        "gf_pg": float(games["gf"].mean()), "ga_pg": float(games["ga"].mean()),
    }


def seasons_in_charge(games: pd.DataFrame, games_per_season: dict[int, int], share: float = 0.6) -> list[int]:
    """Seasons where the manager took at least `share` of the league games, used
    for "best finish". 60% so a caretaker or a manager sacked mid-season is not
    credited with a finish mostly earned by their successor."""
    counts = games.groupby("season").size()
    return [int(s) for s, c in counts.items() if c >= share * games_per_season.get(int(s), 38)]


def season_share(games: pd.DataFrame, games_per_season: dict[int, int]) -> dict[int, float]:
    counts = games.groupby("season").size()
    return {int(s): c / games_per_season.get(int(s), 38) for s, c in counts.items()}


def common_xi(starters: pd.DataFrame) -> dict[str, object] | None:
    """Most-used formation and its most common XI from a starters table
    (one row per starter; columns report_id, formation, player_id, name, top, left)."""
    if starters.empty:
        return None
    per_match = starters.groupby("report_id")["formation"].first().dropna()
    if per_match.empty:
        return None
    formation_counts = per_match.value_counts()
    formation = str(formation_counts.index[0])
    in_form = starters[starters["formation"] == formation]
    # Old list-style reports use template coordinates, newer ones real pitch
    # positions; mixing them would split one position into two "slots".
    inferred = False
    if "inferred" in in_form.columns:
        inferred = bool(in_form.groupby("report_id")["inferred"].first().mean() >= 0.5)
        in_form = in_form[in_form["inferred"] == inferred]
    slot_counts = (in_form.groupby(["top", "left", "player_id", "name"]).size().rename("starts").reset_index()
                   .sort_values("starts", ascending=False))
    slots = in_form.groupby(["top", "left"]).size().sort_values(ascending=False).head(11).index.tolist()
    chosen: dict[tuple[float, float], dict[str, object]] = {}
    used: set[str] = set()
    for r in slot_counts.itertuples(index=False):
        key = (r.top, r.left)
        if key not in slots or key in chosen or r.player_id in used:
            continue
        chosen[key] = {"player_id": r.player_id, "name": r.name, "starts": int(r.starts),
                       "top": float(r.top), "left": float(r.left),
                       "pos": label_position(r.top, r.left, back_three=formation.startswith("3"))}
        used.add(r.player_id)
    xi = sorted(chosen.values(), key=lambda p: (-float(p["top"]), float(p["left"])))  # type: ignore[arg-type]

    # Single most repeated exact XI (same 11 players), if any XI repeats at all.
    sets = starters.groupby("report_id")["player_id"].apply(lambda s: frozenset(s))
    sets = sets[sets.map(len) == 11]
    exact = None
    if len(sets):
        top_set, times = Counter(sets.tolist()).most_common(1)[0]
        if times > 1:
            names = starters[starters["player_id"].isin(top_set)].drop_duplicates("player_id")["name"].tolist()
            exact = {"times": int(times), "players": sorted(names)}
    return {
        "formation": formation,
        "formation_inferred": inferred,
        "formation_matches": int(formation_counts.iloc[0]),
        "matches_with_lineup": int(per_match.size),
        "formations": [{"formation": str(f), "matches": int(c)} for f, c in formation_counts.head(5).items()],
        "xi": xi,
        "exact_xi": exact,
    }


def elo_at(elo_team: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp | None) -> tuple[float | None, float | None]:
    """Rating before the first game in charge and after the last one."""
    g = tenure_games(elo_team, start, end)
    if g.empty:
        return None, None
    return float(g["elo_before"].iloc[0]), float(g["elo"].iloc[-1])


def tenure_net_spend(net_spend: pd.DataFrame, shares: dict[int, float]) -> float | None:
    """Season net spend split by the share of that season's league games managed.
    Transfermarkt season pages carry no transfer dates, so this is an
    approximation (documented): a summer window is credited proportionally."""
    if net_spend.empty or not shares:
        return None
    total = 0.0
    have = False
    for season, share in shares.items():
        row = net_spend[net_spend["season"] == season]
        if not row.empty:
            total += float(row["net_spend"].iloc[0]) * share
            have = True
    return total if have else None


def ppg_timeline(games: pd.DataFrame, window: int = 10) -> list[dict[str, object]]:
    g = games.reset_index(drop=True)
    roll = g["pts"].rolling(window, min_periods=1).mean()
    return [{"i": int(i), "date": d.strftime("%Y-%m-%d"), "pts": int(p), "rolling": round(float(r), 3)}
            for i, (d, p, r) in enumerate(zip(g["date"], g["pts"], roll))]


def coverage(matches_with_lineup: int, games: int) -> float | None:
    return None if games == 0 else matches_with_lineup / games


def rating(value: float | None, lo: float, hi: float) -> int | None:
    """Map a stat onto the 0-99 attribute scale used by the stat panel."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    return int(round(np.clip((value - lo) / (hi - lo), 0, 1) * 99))
