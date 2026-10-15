"""ClubElo ratings (api.clubelo.com), used when the API is reachable.

During this build the API returned HTTP 502 on every attempt, so models/elo.py
computes its own PL-only Elo from match results and this source is optional.
ClubElo includes European games and covers all clubs; ours covers PL games only.
"""
from __future__ import annotations

import io

import pandas as pd

from analysis.ingest.http import fetch

CLUBELO_NAMES = {
    "manchester-united": "ManUnited", "manchester-city": "ManCity", "liverpool": "Liverpool",
    "arsenal": "Arsenal", "chelsea": "Chelsea", "tottenham": "Tottenham",
}


def load_club(team: str) -> pd.DataFrame | None:
    raw = fetch(f"http://api.clubelo.com/{CLUBELO_NAMES[team]}", "clubelo")
    if raw is None:
        return None
    df = pd.read_csv(io.BytesIO(raw))
    df["team"] = team
    return df[["team", "From", "To", "Elo"]].rename(columns={"From": "start", "To": "end", "Elo": "elo"})


def load_all() -> pd.DataFrame | None:
    frames = []
    for team in CLUBELO_NAMES:
        frame = load_club(team)
        if frame is None:
            return None  # all-or-nothing: a partial Elo comparison would mislead
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)
