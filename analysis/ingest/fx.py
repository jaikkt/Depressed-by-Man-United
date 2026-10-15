"""ECB annual average GBP per EUR, to convert Transfermarkt euro figures.

The euro only exists from 1999. Transfermarkt shows pre-1999 fees already
converted to euros, so for seasons before 1999 we apply the 1999 rate; this
is an approximation and is logged in DATA_GAPS.md.
"""
from __future__ import annotations

import io

import pandas as pd

from analysis.ingest.http import fetch

ECB_URL = "https://data-api.ecb.europa.eu/service/data/EXR/A.GBP.EUR.SP00.A?format=csvdata"


def load_gbp_per_eur() -> dict[int, float]:
    raw = fetch(ECB_URL, "ecb")
    if raw is None:
        raise RuntimeError("ECB rates unavailable")
    df = pd.read_csv(io.BytesIO(raw))
    return {int(y): float(v) for y, v in zip(df["TIME_PERIOD"], df["OBS_VALUE"])}


def rate_for_season(rates: dict[int, float], season: int) -> float:
    if season in rates:
        return rates[season]
    if season < min(rates):
        return rates[min(rates)]
    return rates[max(rates)]  # current year not yet published: latest annual rate
