"""Season helpers. One convention everywhere: a season is identified by the
calendar year it *starts* in (1992 = 1992/93), and labelled "1992-93"."""
from __future__ import annotations

import datetime as dt

FIRST_PL_SEASON = 1992


def current_season_start(today: dt.date | None = None) -> int:
    # The PL kicks off in August; before July we're still in last year's season.
    today = today or dt.date.today()
    return today.year if today.month >= 7 else today.year - 1


def season_label(start: int) -> str:
    return f"{start}-{str(start + 1)[-2:]}"


def season_of_date(day: dt.date) -> int:
    return day.year if day.month >= 7 else day.year - 1


def fiscal_year_to_season(fy_end_year: int) -> int:
    """United's financial year ends 30 June, so FY2015 (Jul 2014-Jun 2015)
    maps to the season that ended in it: 2014-15, i.e. start year 2014."""
    return fy_end_year - 1


def games_per_season(start: int) -> int:
    # 22 clubs until 1995-96 made it 42 games; this is why we use PPG, not totals.
    return 42 if start <= 1994 else 38
