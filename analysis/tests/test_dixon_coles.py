import numpy as np
import pandas as pd

from analysis.models.dixon_coles import DCParams, fit, score_matrix, simulate_matches, tau


def synthetic_league(rounds: int = 4, seed: int = 7) -> tuple[DCParams, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    teams = [f"t{i:02d}" for i in range(20)]
    attack = rng.normal(0, 0.3, 20)
    attack -= attack.mean()  # the identifiability constraint the fit also imposes
    defence = rng.normal(0, 0.25, 20)
    truth = DCParams(teams=teams, attack=attack, defence=defence, home_adv=0.25, rho=-0.08)
    home, away = [], []
    for _ in range(rounds):
        for h in teams:
            for a in teams:
                if h != a:
                    home.append(h)
                    away.append(a)
    hg, ag = simulate_matches(truth, home, away, rng)
    df = pd.DataFrame({"home": home, "away": away, "hg": hg, "ag": ag,
                       "date": pd.Timestamp("2020-01-01") + pd.to_timedelta(np.arange(len(home)) // 10, unit="D")})
    return truth, df


def test_parameter_recovery() -> None:
    truth, df = synthetic_league()
    est = fit(df, xi=0.0)
    assert abs(est.attack.sum()) < 1e-6
    assert np.max(np.abs(est.attack - truth.attack)) < 0.2
    assert np.corrcoef(est.attack, truth.attack)[0, 1] > 0.9
    assert np.corrcoef(est.defence, truth.defence)[0, 1] > 0.85
    assert abs(est.home_adv - truth.home_adv) < 0.08
    assert abs(est.rho - truth.rho) < 0.1


def test_score_matrix_is_distribution() -> None:
    m = score_matrix(1.6, 1.1, -0.1)
    assert m.shape == (11, 11)
    assert abs(m.sum() - 1) < 1e-12
    assert (m >= 0).all()


def test_tau_only_touches_low_scores() -> None:
    x = np.array([0, 0, 1, 1, 2, 3])
    y = np.array([0, 1, 0, 1, 2, 0])
    t = tau(x, y, np.full(6, 1.5), np.full(6, 1.2), -0.1)
    assert np.allclose(t[4:], 1.0)
    assert t[0] > 1 and t[3] > 1  # negative rho inflates 0-0 and 1-1


def test_time_decay_downweights_old_matches() -> None:
    _, df = synthetic_league(rounds=1)
    a = fit(df, xi=0.0)
    b = fit(df, xi=0.05)
    assert not np.allclose(a.attack, b.attack)
