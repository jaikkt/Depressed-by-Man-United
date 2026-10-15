import numpy as np
import pandas as pd

from analysis.models.dixon_coles import DCParams
from analysis.models.monte_carlo import convergence, remaining_fixtures, simulate_season, summarise


def params(n: int = 6) -> DCParams:
    teams = [f"t{i}" for i in range(n)]
    attack = np.linspace(0.5, -0.5, n)
    return DCParams(teams=teams, attack=attack, defence=-attack * 0.8, home_adv=0.25, rho=-0.05)


def test_simulation_is_seeded_and_consistent() -> None:
    p = params()
    fx = remaining_fixtures(pd.DataFrame({"home": [], "away": []}), p.teams)
    assert len(fx) == 6 * 5
    a = simulate_season(p, fx, n_sims=2000, seed=1)
    b = simulate_season(p, fx, n_sims=2000, seed=1)
    assert np.array_equal(a.points, b.points)
    # every simulated season ranks each team exactly once
    assert np.all(np.sort(a.positions, axis=1) == np.arange(1, 7))


def test_probabilities_are_sane() -> None:
    p = params()
    fx = remaining_fixtures(pd.DataFrame({"home": [], "away": []}), p.teams)
    s = summarise(simulate_season(p, fx, n_sims=4000), relegation_places=1)
    assert abs(s["p_title"].sum() - 1) < 1e-9
    assert abs(s["p_relegation"].sum() - 1) < 1e-9
    assert s.loc[0, "p_title"] > s.loc[5, "p_title"]  # strongest team wins most often
    assert (s["p5"] <= s["p50"]).all() and (s["p50"] <= s["p95"]).all()


def test_fixed_results_are_added() -> None:
    p = params(4)
    played = pd.DataFrame({"home": ["t0"], "away": ["t1"], "hg": [3], "ag": [0]})
    fx = remaining_fixtures(played, p.teams)
    assert ("t0", "t1") not in fx and len(fx) == 11
    sim = simulate_season(p, fx, fixed=played, n_sims=500)
    assert sim.points[:, 0].min() >= 3


def test_convergence_checkpoints() -> None:
    p = params()
    fx = remaining_fixtures(pd.DataFrame({"home": [], "away": []}), p.teams)
    conv = convergence(simulate_season(p, fx, n_sims=1000), "t0", [100, 500, 1000])
    assert [c["n"] for c in conv] == [100, 500, 1000]
