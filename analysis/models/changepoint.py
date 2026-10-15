"""Change-point detection on United's form, with penalty sensitivity.

PELT (Pruned Exact Linear Time) finds the set of breakpoints that minimises
total within-segment cost + penalty * number of breaks. The penalty is a
free choice, and a different penalty gives different breaks, which makes it
easy to cherry-pick a story. So we sweep a range of penalties and report how
often each break appears; only breaks that survive most penalties are
treated as real.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import ruptures as rpt

PENALTIES = [10, 20, 30, 40, 60, 90, 130]
ROLL = 19  # half a season


def rolling_ppg(match_log: pd.DataFrame, team: str, window: int = ROLL) -> pd.DataFrame:
    t = match_log[match_log["team"] == team].sort_values("date").reset_index(drop=True)
    t["rolling_ppg"] = t["pts"].rolling(window).mean()
    return t.dropna(subset=["rolling_ppg"]).reset_index(drop=True)


def detect(signal: np.ndarray, penalty: float, min_size: int = 19) -> list[int]:
    """Return breakpoint indices (exclusive segment ends, final index removed)."""
    z = (signal - signal.mean()) / (signal.std() or 1.0)  # standardise so penalties are comparable
    algo = rpt.Pelt(model="l2", min_size=min_size, jump=1).fit(z.reshape(-1, 1))
    return [b for b in algo.predict(pen=penalty) if b < len(signal)]


def sensitivity(signal: np.ndarray, penalties: list[float] = PENALTIES, tolerance: int = 10, min_size: int = 19) -> pd.DataFrame:
    """For each break found at any penalty, the share of penalties at which a
    break occurs within `tolerance` matches of it."""
    runs = {p: detect(signal, p, min_size) for p in penalties}
    candidates = sorted({b for bs in runs.values() for b in bs})
    merged: list[int] = []
    for b in candidates:
        if not merged or b - merged[-1] > tolerance:
            merged.append(b)
    rows = []
    for b in merged:
        hits = sum(any(abs(b - x) <= tolerance for x in bs) for bs in runs.values())
        rows.append({"index": b, "support": hits / len(penalties)})
    return pd.DataFrame(rows, columns=["index", "support"])


def segment_means(signal: np.ndarray, breaks: list[int]) -> list[tuple[int, int, float]]:
    edges = [0, *sorted(breaks), len(signal)]
    return [(s, e, float(signal[s:e].mean())) for s, e in zip(edges[:-1], edges[1:]) if e > s]
