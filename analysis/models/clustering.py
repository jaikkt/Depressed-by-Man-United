"""Group manager tenures into "types" with k-means.

Each tenure (United + comparison clubs, at least 19 league games) becomes a
vector: PPG, net spend per season (real £), average squad age, Elo change per
season. Features are standardised first, because k-means uses Euclidean
distance and would otherwise be dominated by whichever feature has the
biggest units (pounds!). k is chosen by silhouette score, and PCA projects
the vectors to 2D purely for display.
xG difference would be a fifth feature, but no xG source was available.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

FEATURES = ["ppg", "net_spend_per_season", "avg_squad_age", "elo_change_per_season"]


def prepare(df: pd.DataFrame, features: list[str]) -> np.ndarray:
    """Make features k-means friendly before standardising:
    * net spend is heavy-tailed (one £500m+ season would form a cluster of its
      own), so it goes on an asinh scale, which acts like log but handles
      negative net spend (selling clubs);
    * every feature is winsorised at the 5th/95th percentile so a short,
      extreme tenure can't drag a centre around."""
    X = df[features].to_numpy(dtype=float).copy()
    if "net_spend_per_season" in features:
        j = features.index("net_spend_per_season")
        X[:, j] = np.arcsinh(X[:, j] / 1e7)
    lo, hi = np.percentile(X, 5, axis=0), np.percentile(X, 95, axis=0)
    return np.clip(X, lo, hi)


@dataclass
class ClusterResult:
    k: int
    silhouettes: dict[int, float]
    labels: np.ndarray
    coords: np.ndarray  # (n, 2) PCA
    explained: list[float]
    centers: pd.DataFrame  # in original units (mean of members)
    centers_z: pd.DataFrame  # standardised, used for naming


def choose_k(X: np.ndarray, k_range: range = range(2, 7), seed: int = 0) -> dict[int, float]:
    scores = {}
    for k in k_range:
        if k >= len(X):
            break
        labels = KMeans(n_clusters=k, n_init=20, random_state=seed).fit_predict(X)
        scores[k] = float(silhouette_score(X, labels))
    return scores


def cluster_tenures(df: pd.DataFrame, features: list[str] = FEATURES, seed: int = 0) -> ClusterResult:
    scaler = StandardScaler()
    X = scaler.fit_transform(prepare(df, features))
    sil = choose_k(X, seed=seed)
    k = max(sil, key=lambda key: sil[key])
    km = KMeans(n_clusters=k, n_init=50, random_state=seed).fit(X)
    pca = PCA(n_components=2, random_state=seed).fit(X)
    centers = df.assign(_label=km.labels_).groupby("_label")[features].mean().reset_index(drop=True)
    centers_z = pd.DataFrame(km.cluster_centers_, columns=features)
    return ClusterResult(k=k, silhouettes=sil, labels=km.labels_, coords=pca.transform(X),
                         explained=[float(v) for v in pca.explained_variance_ratio_], centers=centers, centers_z=centers_z)


def name_clusters(centers_z: pd.DataFrame) -> list[str]:
    """Plain-language label per cluster from its standardised centre (z-scores:
    0 = average tenure). Labels describe the centre, not each member."""
    names = []
    for r in centers_z.itertuples(index=False):
        rich = r.net_spend_per_season > 0.25
        if r.ppg > 0.5:
            name = "BIG-SPEND WINNERS" if rich else "EFFICIENT WINNERS"
        elif r.ppg < -0.5:
            name = "EXPENSIVE DECLINE" if rich else "LOW-BUDGET STRUGGLE"
        elif r.elo_change_per_season > 0.3:
            name = "RISING PROJECTS"
        elif r.elo_change_per_season < -0.3:
            name = "SLOW DECLINE"
        else:
            name = "SPEND AND HOPE" if rich else "STEADY MIDFIELD"
        names.append(name)
    seen: dict[str, int] = {}
    out = []
    for n in names:
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else f"{n} {seen[n]}")
    return out


def regression_to_mean(table: pd.DataFrame, trend_window: int = 3) -> pd.DataFrame:
    """For each club-season: deviation from the club's previous-3-season PPG
    trend, and the change in PPG the following season. A negative slope across
    clubs is regression to the mean."""
    rows = []
    for team, g in table.sort_values("season").groupby("team"):
        g = g.set_index("season")
        for s in g.index:
            prev = [s - i for i in range(1, trend_window + 1)]
            if not all(p in g.index for p in prev) or (s + 1) not in g.index:
                continue
            trend = float(g.loc[prev, "ppg"].mean())
            rows.append({"team": team, "season": s, "deviation": float(g.loc[s, "ppg"]) - trend,
                         "next_change": float(g.loc[s + 1, "ppg"] - g.loc[s, "ppg"])})
    return pd.DataFrame(rows)


def slope(x: pd.Series, y: pd.Series) -> float:
    return float(np.polyfit(x, y, 1)[0]) if len(x) > 2 else float("nan")
