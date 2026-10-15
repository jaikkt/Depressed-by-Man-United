"""Currency + inflation: every money figure on the site is in pounds at the
latest available CPI price level ("real £")."""
from __future__ import annotations

import pandas as pd

from analysis.ingest.fx import rate_for_season


def eur_to_gbp(eur: pd.Series, season: pd.Series, gbp_per_eur: dict[int, float]) -> pd.Series:
    return eur * season.map(lambda s: rate_for_season(gbp_per_eur, int(s)))


def to_real(gbp: pd.Series, season: pd.Series, cpi: pd.DataFrame) -> pd.Series:
    factor = cpi.set_index("season")["to_latest"]
    latest = float(factor.iloc[-1])
    return gbp * season.map(lambda s: float(factor.get(int(s), latest)))
