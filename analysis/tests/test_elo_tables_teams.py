import pandas as pd

from analysis.clean.seasons import fiscal_year_to_season, season_label
from analysis.clean.tables import league_table, ppg_to_position
from analysis.clean.teams import canonical
from analysis.models.elo import expected_score, run_elo


def toy_results() -> pd.DataFrame:
    return pd.DataFrame({
        "season": [2000] * 6,
        "date": pd.to_datetime(["2000-08-01", "2000-08-01", "2000-08-08", "2000-08-08", "2000-08-15", "2000-08-15"]),
        "home": ["a", "c", "b", "a", "c", "b"],
        "away": ["b", "d", "c", "d", "a", "d"],
        "hg": [2, 0, 1, 3, 0, 2],
        "ag": [0, 0, 1, 1, 1, 2],
    })


def test_canonical_names() -> None:
    for raw in ["Man United", "Manchester Utd", "Man Utd", "Manchester United FC", "ManUnited"]:
        assert canonical(raw) == "manchester-united"
    assert canonical("Spurs") == "tottenham"
    assert canonical("Nott'm Forest") == "nottingham-forest"
    assert canonical("Wimbledon FC (- 2004)") == "wimbledon"


def test_season_helpers() -> None:
    assert season_label(1992) == "1992-93"
    assert fiscal_year_to_season(2015) == 2014


def test_league_table_ppg_and_order() -> None:
    t = league_table(toy_results())
    assert list(t["team"])[0] == "a"
    a = t.set_index("team").loc["a"]
    assert a["pts"] == 9 and a["played"] == 3 and abs(a["ppg"] - 3.0) < 1e-12
    assert ppg_to_position(3.0, t) == 1.0


def test_elo_is_zero_sum_and_favours_winners() -> None:
    elo = run_elo(toy_results())
    final = elo.sort_values("date").groupby("team").tail(1).set_index("team")["elo"]
    assert abs(final.sum() - 4 * 1500) < 1e-6
    assert final["a"] == final.max()
    assert expected_score(1500, 1500, 65) > 0.5  # home advantage
