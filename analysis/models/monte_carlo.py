"""Monte Carlo season simulation on top of Dixon-Coles strengths.

For a finished season we replay every fixture 10,000 times with the season's
fitted strengths: the spread of simulated points shows how much of a final
total was skill versus luck. For the season in progress, games already played
keep their real result and only the remaining fixtures are simulated.

Vectorised: each fixture is one inverse-CDF lookup across all simulations at
once, and team totals are a matrix product with a fixture->team indicator.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from analysis.models.dixon_coles import DCParams, score_matrix

N_SIMS = 10_000
SEED = 1992
CHECKPOINTS = [100, 250, 500, 1000, 2500, 5000, 10000]


@dataclass
class SimResult:
    teams: list[str]
    points: np.ndarray  # (n_sims, n_teams)
    positions: np.ndarray  # (n_sims, n_teams), 1 = champion


def remaining_fixtures(played: pd.DataFrame, teams: list[str]) -> list[tuple[str, str]]:
    """Every ordered pair plays once in a double round robin; whatever pair is
    missing from `played` is still to come."""
    done = set(zip(played["home"], played["away"]))
    return [(h, a) for h in teams for a in teams if h != a and (h, a) not in done]


def simulate_season(params: DCParams, fixtures: list[tuple[str, str]], fixed: pd.DataFrame | None = None,
                    n_sims: int = N_SIMS, seed: int = SEED) -> SimResult:
    rng = np.random.default_rng(seed)
    teams = params.teams
    idx = params.index()
    n_t = len(teams)
    hi = np.array([idx[h] for h, _ in fixtures], dtype=int)
    ai = np.array([idx[a] for _, a in fixtures], dtype=int)
    lam, mu = params.rates(hi, ai)

    n_f = len(fixtures)
    hg = np.empty((n_sims, n_f), dtype=np.int16)
    ag = np.empty((n_sims, n_f), dtype=np.int16)
    for k in range(n_f):
        cdf = np.cumsum(score_matrix(float(lam[k]), float(mu[k]), params.rho).ravel())
        cell = np.searchsorted(cdf, rng.random(n_sims) * cdf[-1])
        hg[:, k], ag[:, k] = np.divmod(cell, 11)

    home_ind = np.zeros((n_f, n_t))
    away_ind = np.zeros((n_f, n_t))
    home_ind[np.arange(n_f), hi] = 1
    away_ind[np.arange(n_f), ai] = 1
    hp = np.where(hg > ag, 3, np.where(hg == ag, 1, 0))
    apts = np.where(ag > hg, 3, np.where(hg == ag, 1, 0))
    points = hp @ home_ind + apts @ away_ind
    gd = (hg - ag) @ home_ind + (ag - hg) @ away_ind
    gf = hg @ home_ind + ag @ away_ind

    if fixed is not None and len(fixed):
        base_pts = np.zeros(n_t)
        base_gd = np.zeros(n_t)
        base_gf = np.zeros(n_t)
        for g in fixed.itertuples(index=False):
            h, a = idx[g.home], idx[g.away]
            base_pts[h] += 3 if g.hg > g.ag else 1 if g.hg == g.ag else 0
            base_pts[a] += 3 if g.ag > g.hg else 1 if g.hg == g.ag else 0
            base_gd[h] += g.hg - g.ag
            base_gd[a] += g.ag - g.hg
            base_gf[h] += g.hg
            base_gf[a] += g.ag
        points = points + base_pts
        gd = gd + base_gd
        gf = gf + base_gf

    # PL tie-breaks: points, then goal difference, then goals scored; a tiny
    # random jitter settles exact ties instead of always favouring index order.
    score = points * 1e6 + (gd + 500) * 1e3 + gf + rng.random(points.shape) * 0.1
    order = np.argsort(-score, axis=1)
    positions = np.empty_like(order)
    rows = np.arange(n_sims)[:, None]
    positions[rows, order] = np.arange(1, n_t + 1)
    return SimResult(teams=teams, points=points.astype(int), positions=positions)


def summarise(sim: SimResult, relegation_places: int = 3) -> pd.DataFrame:
    n_t = len(sim.teams)
    pct = np.percentile(sim.points, [5, 25, 50, 75, 95], axis=0)
    return pd.DataFrame({
        "team": sim.teams,
        "p5": pct[0], "p25": pct[1], "p50": pct[2], "p75": pct[3], "p95": pct[4],
        "mean_points": sim.points.mean(axis=0),
        "p_title": (sim.positions == 1).mean(axis=0),
        "p_top4": (sim.positions <= 4).mean(axis=0),
        "p_relegation": (sim.positions > n_t - relegation_places).mean(axis=0),
        "exp_position": sim.positions.mean(axis=0),
    })


def convergence(sim: SimResult, team: str, checkpoints: list[int] = CHECKPOINTS) -> list[dict[str, float]]:
    """Running estimate of P(title) and P(top 4) as more simulations are added.
    If the curve is flat well before 10,000, the run count is sufficient."""
    j = sim.teams.index(team)
    title = np.cumsum(sim.positions[:, j] == 1)
    top4 = np.cumsum(sim.positions[:, j] <= 4)
    out = []
    for n in checkpoints:
        if n <= len(title):
            out.append({"n": n, "p_title": float(title[n - 1] / n), "p_top4": float(top4[n - 1] / n)})
    return out


def points_histogram(sim: SimResult, team: str) -> dict[int, float]:
    j = sim.teams.index(team)
    values, counts = np.unique(sim.points[:, j], return_counts=True)
    return {int(v): float(c / len(sim.points)) for v, c in zip(values, counts)}
