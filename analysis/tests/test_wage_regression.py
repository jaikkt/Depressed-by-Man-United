import numpy as np
import pandas as pd

from analysis.clean.tables import league_table
from analysis.models.wage_regression import add_place_residuals, fit_resource_model, net_spend_by_club_season, relative_resource


def fake_league(seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for season in range(2005, 2015):
        values = rng.lognormal(4, 0.7, 20)
        rel = values / values.mean()
        ppg = 1.4 + 0.6 * np.log(rel) + rng.normal(0, 0.15, 20)
        for i in range(20):
            rows.append({"season": season, "team": f"t{i}", "value": values[i], "ppg": ppg[i], "played": 38})
    df = pd.DataFrame(rows)
    df["position"] = df.groupby("season")["ppg"].rank(ascending=False, method="first").astype(int)
    return df


def test_relative_resource_is_one_on_average() -> None:
    rel = relative_resource(fake_league(), "value")
    assert np.allclose(rel.groupby("season")["rel"].mean(), 1.0)


def test_model_recovers_slope_and_residuals_center_on_zero() -> None:
    model, data = fit_resource_model(fake_league(), "value")
    assert abs(model.slope - 0.6) < 0.08
    assert abs(model.intercept - 1.4) < 0.08
    assert abs(data["residual"].mean()) < 1e-9


def test_place_residual_sign() -> None:
    df = fake_league()
    _, data = fit_resource_model(df, "value")
    table = df[["season", "team", "ppg", "position"]]
    out = add_place_residuals(data, table)
    # a club whose actual PPG beats its prediction finishes higher than "expected"
    over = out.sort_values("residual").iloc[-1]
    assert over["places_vs_model"] > 0


def test_net_spend_ignores_unknown_fees_and_loans() -> None:
    t = pd.DataFrame({
        "season": [2010] * 4, "team": ["a"] * 4, "direction": ["in", "in", "out", "in"],
        "is_loan": [False, False, False, True], "fee_gbp_real": [10.0, None, 4.0, 99.0],
    })
    ns = net_spend_by_club_season(t)
    assert ns.loc[0, "net_spend"] == 6.0


def test_league_table_feeds_model() -> None:
    results = pd.DataFrame({"season": [2010, 2010], "date": pd.to_datetime(["2010-08-01", "2010-08-02"]),
                            "home": ["a", "b"], "away": ["b", "a"], "hg": [1, 0], "ag": [0, 0]})
    t = league_table(results)
    assert set(t.columns) >= {"ppg", "position", "played"}
