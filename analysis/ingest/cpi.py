"""UK CPI (ONS series D7BT, 2015=100) for inflation adjustment.

Method: each season's price level is the mean of its monthly CPI from July to
June. Money is restated in "latest money" by multiplying by
CPI_latest_month / CPI_season. CPI rather than RPI because RPI is no longer a
National Statistic; football wage inflation is far higher than CPI, which is
why the wage model uses wages *relative to the league average* instead.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd

from analysis.ingest.http import fetch

CPI_URL = "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23"
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def parse_monthly(raw: bytes) -> pd.DataFrame:
    rows = []
    for rec in csv.reader(io.StringIO(raw.decode("utf-8-sig"))):
        if len(rec) < 2 or not rec[1].strip():
            continue
        parts = rec[0].split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1] in MONTHS:
            rows.append({"year": int(parts[0]), "month": MONTHS[parts[1]], "cpi": float(rec[1])})
    return pd.DataFrame(rows)


def season_index(monthly: pd.DataFrame) -> pd.DataFrame:
    m = monthly.copy()
    m["season"] = m["year"].where(m["month"] >= 7, m["year"] - 1)
    out = m.groupby("season")["cpi"].mean().rename("cpi_season").reset_index()
    latest = m.sort_values(["year", "month"]).iloc[-1]
    out["cpi_latest"] = latest["cpi"]
    out["to_latest"] = out["cpi_latest"] / out["cpi_season"]
    out.attrs["latest_label"] = f"{int(latest['year'])}-{int(latest['month']):02d}"
    return out


def load_season_index() -> pd.DataFrame:
    raw = fetch(CPI_URL, "ons")
    if raw is None:
        raise RuntimeError("ONS CPI unavailable")
    return season_index(parse_monthly(raw))


def main() -> None:
    df = load_season_index()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "cpi_season.parquet", index=False)
    print("latest month:", df.attrs["latest_label"])
    print(df.tail(5).to_string())


if __name__ == "__main__":
    main()
