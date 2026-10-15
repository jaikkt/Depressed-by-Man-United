"""Dixon-Coles (1997) team-strength model.

Goals in a match are modelled as (nearly) independent Poisson variables:
    log(lambda_home) = attack[home] + defence[away] + home_adv
    log(mu_away)     = attack[away] + defence[home]
"defence" here is a *leakiness* parameter: higher means you concede more.

Dixon & Coles noticed real football has more 0-0 and 1-1 draws (and fewer
1-0 / 0-1) than independent Poissons predict, so they multiply the
probability of those four low scores by a correction tau(rho).

Older matches matter less: each match is weighted by exp(-xi * days_ago).

The model is only identified up to a constant (add c to every attack and
subtract c from every defence and nothing changes), so we impose
sum(attack) = 0 as an equality constraint in scipy.optimize.minimize.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

DEFAULT_XI = 0.0019  # per day; Dixon & Coles' choice, a half-life of about a year


@dataclass
class DCParams:
    teams: list[str]
    attack: np.ndarray  # log scale, sums to 0
    defence: np.ndarray  # log scale
    home_adv: float  # log scale
    rho: float

    def rates(self, home: np.ndarray, away: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        lam = np.exp(self.attack[home] + self.defence[away] + self.home_adv)
        mu = np.exp(self.attack[away] + self.defence[home])
        return lam, mu

    def index(self) -> dict[str, int]:
        return {t: i for i, t in enumerate(self.teams)}


def tau(x: np.ndarray, y: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    out = np.ones_like(lam, dtype=float)
    m00 = (x == 0) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m10 = (x == 1) & (y == 0)
    m11 = (x == 1) & (y == 1)
    out[m00] = 1 - lam[m00] * mu[m00] * rho
    out[m01] = 1 + lam[m01] * rho
    out[m10] = 1 + mu[m10] * rho
    out[m11] = 1 - rho
    return out


def time_weights(dates: pd.Series, xi: float, ref: pd.Timestamp | None = None) -> np.ndarray:
    ref = ref if ref is not None else dates.max()
    days = (ref - dates).dt.days.to_numpy().astype(float)
    return np.exp(-xi * days)


def _unpack(theta: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray, float, float]:
    return theta[:n], theta[n:2 * n], float(theta[2 * n]), float(theta[2 * n + 1])


def neg_log_likelihood(theta: np.ndarray, h: np.ndarray, a: np.ndarray, x: np.ndarray, y: np.ndarray,
                       w: np.ndarray, n: int) -> tuple[float, np.ndarray]:
    """Weighted negative log-likelihood and its analytic gradient.
    Writing the gradient by hand makes each season fit take well under a second."""
    att, dfn, gam, rho = _unpack(theta, n)
    log_lam = att[h] + dfn[a] + gam
    log_mu = att[a] + dfn[h]
    lam, mu = np.exp(log_lam), np.exp(log_mu)
    t = tau(x, y, lam, mu, rho)
    t = np.clip(t, 1e-10, None)
    ll = np.log(t) + x * log_lam - lam - gammaln(x + 1) + y * log_mu - mu - gammaln(y + 1)
    nll = -float(np.sum(w * ll))

    # d(ll)/d(log lambda) and d(ll)/d(log mu): Poisson part plus the tau part.
    m00 = (x == 0) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m10 = (x == 1) & (y == 0)
    m11 = (x == 1) & (y == 1)
    d_lam = x - lam
    d_mu = y - mu
    d_lam = d_lam + np.where(m00, -lam * mu * rho / t, 0.0) + np.where(m01, lam * rho / t, 0.0)
    d_mu = d_mu + np.where(m00, -lam * mu * rho / t, 0.0) + np.where(m10, mu * rho / t, 0.0)
    d_rho = np.where(m00, -lam * mu / t, 0.0) + np.where(m01, lam / t, 0.0) + np.where(m10, mu / t, 0.0) + np.where(m11, -1.0 / t, 0.0)

    g = np.zeros_like(theta)
    np.add.at(g, h, w * d_lam)  # attack[home] via lambda
    np.add.at(g, a, w * d_mu)  # attack[away] via mu
    np.add.at(g, n + a, w * d_lam)  # defence[away] via lambda
    np.add.at(g, n + h, w * d_mu)  # defence[home] via mu
    g[2 * n] = np.sum(w * d_lam)
    g[2 * n + 1] = np.sum(w * d_rho)
    return nll, -g


def fit(matches: pd.DataFrame, xi: float = DEFAULT_XI, ref: pd.Timestamp | None = None) -> DCParams:
    """Fit by maximum likelihood. `matches` needs home, away, hg, ag, date."""
    teams = sorted(set(matches["home"]) | set(matches["away"]))
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    h = matches["home"].map(idx).to_numpy()
    a = matches["away"].map(idx).to_numpy()
    x = matches["hg"].to_numpy().astype(float)
    y = matches["ag"].to_numpy().astype(float)
    w = time_weights(matches["date"], xi, ref) if xi > 0 else np.ones(len(matches))

    theta0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25, -0.05]])
    bounds = [(-3, 3)] * (2 * n) + [(-1, 1), (-0.4, 0.4)]
    constraint = {"type": "eq", "fun": lambda th: np.sum(th[:n]), "jac": lambda th: np.concatenate([np.ones(n), np.zeros(n + 2)])}
    res = minimize(
        neg_log_likelihood, theta0, args=(h, a, x, y, w, n), jac=True, method="SLSQP",
        bounds=bounds, constraints=[constraint], options={"maxiter": 500, "ftol": 1e-9},
    )
    att, dfn, gam, rho = _unpack(res.x, n)
    return DCParams(teams=teams, attack=att, defence=dfn, home_adv=gam, rho=rho)


def score_matrix(lam: float, mu: float, rho: float, max_goals: int = 10) -> np.ndarray:
    """P(home=i, away=j) for i, j in 0..max_goals, renormalised after truncation."""
    goals = np.arange(max_goals + 1)
    ph = np.exp(goals * np.log(lam) - lam - gammaln(goals + 1))
    pa = np.exp(goals * np.log(mu) - mu - gammaln(goals + 1))
    m = np.outer(ph, pa)
    m[0, 0] *= 1 - lam * mu * rho
    m[0, 1] *= 1 + lam * rho
    m[1, 0] *= 1 + mu * rho
    m[1, 1] *= 1 - rho
    m = np.clip(m, 0, None)
    return m / m.sum()


def simulate_matches(params: DCParams, home: list[str], away: list[str], rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Draw one score per fixture (used by tests to create synthetic leagues)."""
    idx = params.index()
    hi = np.array([idx[t] for t in home])
    ai = np.array([idx[t] for t in away])
    lam, mu = params.rates(hi, ai)
    hg = np.empty(len(home), dtype=int)
    ag = np.empty(len(home), dtype=int)
    for k in range(len(home)):
        m = score_matrix(float(lam[k]), float(mu[k]), params.rho).ravel()
        cell = rng.choice(m.size, p=m)
        hg[k], ag[k] = divmod(cell, 11)
    return hg, ag
