"""Premier League match results.

football-data.co.uk is the primary source (results + bookmaker odds) from
1993/94. Its 1992/93 file is missing, so that one season is backfilled from
the engsoccerdata project (James Curley, GitHub), which compiles English
results back to 1888. Both are cached in data/raw/.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd

from analysis.clean.seasons import current_season_start, FIRST_PL_SEASON
from analysis.clean.teams import canonical
from analysis.ingest.http import fetch

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
ENGSOCCER_URL = "https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/england.csv"
COLUMNS = ["season", "date", "home", "away", "hg", "ag", "odds_h", "odds_d", "odds_a", "source"]


def football_data_url(season: int) -> str:
    code = f"{str(season)[-2:]}{str(season + 1)[-2:]}"
    return f"https://www.football-data.co.uk/mmz4281/{code}/E0.csv"


def _odds_columns(df: pd.DataFrame) -> tuple[str, str, str] | None:
    # Average odds were published under different names over the years;
    # fall back through the most consistent books.
    for h, d, a in [("AvgH", "AvgD", "AvgA"), ("BbAvH", "BbAvD", "BbAvA"), ("B365H", "B365D", "B365A"),
                    ("WHH", "WHD", "WHA"), ("IWH", "IWD", "IWA"), ("LBH", "LBD", "LBA")]:
        if {h, d, a} <= set(df.columns) and df[h].notna().mean() > 0.9:
            return h, d, a
    return None


def parse_football_data(raw: bytes, season: int) -> pd.DataFrame:
    text = raw.decode("utf-8-sig", errors="replace")
    # Some seasons (e.g. 2003-05) have rows with trailing extra fields. Skipping
    # "bad lines" silently lost 45 matches a season, so trim rows to the header.
    rows = [r for r in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in r)]
    header = rows[0]
    df = pd.DataFrame([(r + [""] * len(header))[: len(header)] for r in rows[1:]], columns=header)
    df = df.replace("", pd.NA)
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    out = pd.DataFrame({
        "season": season,
        "date": pd.to_datetime(df["Date"], dayfirst=True, format="mixed"),
        "home": df["HomeTeam"].map(canonical),
        "away": df["AwayTeam"].map(canonical),
        "hg": df["FTHG"].astype(int),
        "ag": df["FTAG"].astype(int),
    })
    odds = _odds_columns(df)
    for col, src in zip(["odds_h", "odds_d", "odds_a"], odds or (None, None, None)):
        out[col] = pd.to_numeric(df[src], errors="coerce") if src else float("nan")
    out["source"] = "football-data.co.uk"
    return out[COLUMNS]


def parse_engsoccer(raw: bytes, season: int) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw), low_memory=False)
    df = df[(df["Season"] == season) & (df["tier"] == 1)]
    out = pd.DataFrame({
        "season": season,
        "date": pd.to_datetime(df["Date"]),
        "home": df["home"].map(canonical),
        "away": df["visitor"].map(canonical),
        "hg": df["hgoal"].astype(int),
        "ag": df["vgoal"].astype(int),
        "odds_h": float("nan"), "odds_d": float("nan"), "odds_a": float("nan"),
        "source": "engsoccerdata",
    })
    return out[COLUMNS]


def load_results(last_season: int | None = None) -> pd.DataFrame:
    last_season = last_season or current_season_start()
    frames: list[pd.DataFrame] = []
    for season in range(FIRST_PL_SEASON, last_season + 1):
        raw = fetch(football_data_url(season), "football_data")
        if raw is not None and b"HomeTeam" in raw[:400]:
            frames.append(parse_football_data(raw, season))
            continue
        eng = fetch(ENGSOCCER_URL, "engsoccerdata")
        if eng is not None:
            part = parse_engsoccer(eng, season)
            if len(part):
                frames.append(part)
                continue
        print(f"[results] no source for season {season}")
    df = pd.concat(frames, ignore_index=True).sort_values(["date", "home"]).reset_index(drop=True)
    return df


def main() -> None:
    df = load_results()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "results.parquet", index=False)
    print(df.groupby("season").size().to_string())


if __name__ == "__main__":
    main()


def load_warmup(first: int = 1985, last: int = FIRST_PL_SEASON - 1) -> pd.DataFrame:
    """Old First Division seasons, used only to warm up Elo ratings so that
    clubs don't all start the Premier League era at the same rating."""
    raw = fetch(ENGSOCCER_URL, "engsoccerdata")
    if raw is None:
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat([parse_engsoccer(raw, s) for s in range(first, last + 1)], ignore_index=True)
