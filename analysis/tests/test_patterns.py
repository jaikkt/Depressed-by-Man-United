import numpy as np
import pandas as pd

from analysis.models.changepoint import detect, segment_means, sensitivity
from analysis.models.clustering import cluster_tenures, name_clusters, prepare, regression_to_mean, slope
from analysis.models.manager_bounce import aligned_points, bounce_curve, bounce_stat, manager_changes


def test_changepoint_finds_planted_break() -> None:
    rng = np.random.default_rng(0)
    sig = np.concatenate([rng.normal(2.0, 0.1, 200), rng.normal(1.4, 0.1, 200)])
    breaks = detect(sig, penalty=20)
    assert any(abs(b - 200) <= 5 for b in breaks)
    sens = sensitivity(sig)
    top = sens.sort_values("support").iloc[-1]
    assert abs(top["index"] - 200) <= 10 and top["support"] == 1.0
    segs = segment_means(sig, [200])
    assert segs[0][2] > segs[1][2]


def test_flat_signal_has_no_robust_breaks() -> None:
    rng = np.random.default_rng(1)
    sens = sensitivity(rng.normal(1.6, 0.1, 400))
    assert (sens["support"] < 0.5).all() if len(sens) else True


def toy_log() -> pd.DataFrame:
    dates = pd.date_range("2000-08-01", periods=60, freq="7D")
    pts = [0] * 30 + [3] * 30  # terrible under the old manager, perfect under the new one
    return pd.DataFrame({"team": "x", "date": dates, "pts": pts})


def test_bounce_alignment() -> None:
    log = toy_log()
    coaches = pd.DataFrame({"team": ["x", "x"], "manager": ["old", "new"],
                            "start": [pd.Timestamp("1999-01-01"), log["date"][30]], "end": [log["date"][30], pd.NaT]})
    ch = manager_changes(coaches, log)
    assert list(ch["manager"]) == ["new"] and ch.loc[0, "first_idx"] == 30
    curve = bounce_curve(aligned_points(ch, log), smooth=1).set_index("rel")["mean"]
    assert curve[-1] == 0 and curve[0] == 3


def test_bounce_stat() -> None:
    first, rest = bounce_stat(np.array([3] * 10 + [0] * 10))
    assert first == 3 and rest == 0
    assert bounce_stat(np.array([])) == (None, None)


def test_clustering_separates_obvious_groups() -> None:
    rng = np.random.default_rng(2)
    a = pd.DataFrame({"ppg": rng.normal(2.2, 0.05, 15), "net_spend_per_season": rng.normal(8e7, 5e6, 15),
                      "avg_squad_age": rng.normal(27, 0.3, 15), "elo_change_per_season": rng.normal(20, 3, 15)})
    b = pd.DataFrame({"ppg": rng.normal(1.1, 0.05, 15), "net_spend_per_season": rng.normal(1e6, 5e5, 15),
                      "avg_squad_age": rng.normal(24, 0.3, 15), "elo_change_per_season": rng.normal(-20, 3, 15)})
    df = pd.concat([a, b], ignore_index=True)
    res = cluster_tenures(df)
    assert res.k == 2
    assert len(set(res.labels[:15])) == 1 and len(set(res.labels[15:])) == 1
    names = name_clusters(res.centers_z)
    assert any("WINNERS" in n for n in names)
    assert prepare(df, ["net_spend_per_season"]).shape == (30, 1)


def test_regression_to_mean_slope_negative_for_noise() -> None:
    rng = np.random.default_rng(5)
    rows = [{"team": f"t{t}", "season": s, "ppg": 1.4 + rng.normal(0, 0.3)} for t in range(20) for s in range(2000, 2020)]
    rtm = regression_to_mean(pd.DataFrame(rows))
    assert slope(rtm["deviation"], rtm["next_change"]) < -0.5
