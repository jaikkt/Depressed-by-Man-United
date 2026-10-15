"""The JSON contract between the Python pipeline and the website.

Every JSON file export.py writes is described here as a TypedDict.
`typescript_definitions()` turns these classes into TypeScript interfaces
(web/lib/data-types.ts), so if a field is renamed here the site stops
compiling instead of silently showing blanks. One source of truth, two languages.
"""
from __future__ import annotations

import types
import typing
from typing import Literal, TypedDict, Union, get_args, get_origin, get_type_hints

# ---------- shared ---------------------------------------------------------------


class Credit(TypedDict):
    slug: str
    name: str
    title: str
    author: str
    license: str
    source_url: str


class SigningCard(TypedDict):
    team: str
    player: str
    player_id: str
    season: int
    season_label: str
    age: int | None
    position: str
    from_club: str
    fee_gbp_real: float
    league_minutes: int
    starts: int
    ga_per90: float | None
    years_at_club: float
    sale_fee_gbp_real: float | None
    still_at_club: bool
    net_cost_gbp_real: float
    cost_per_1000_min: float | None
    regular_share: float
    value_rating: int
    signed_under: str | None


# ---------- menu -----------------------------------------------------------------


class MenuData(TypedDict):
    generated: str
    current_season_label: str
    headlines: list[str]
    tips: list[str]
    hero_stat: str


# ---------- managers -------------------------------------------------------------


class XIPlayer(TypedDict):
    player_id: str
    name: str
    starts: int
    top: float
    left: float
    pos: str


class FormationCount(TypedDict):
    formation: str
    matches: int


class ExactXI(TypedDict):
    times: int
    players: list[str]


class Lineup(TypedDict):
    label: str
    formation: str
    formation_inferred: bool
    formation_matches: int
    matches_with_lineup: int
    league_games: int
    coverage: float | None
    formations: list[FormationCount]
    xi: list[XIPlayer]
    exact_xi: ExactXI | None


class Trophy(TypedDict):
    date: str
    competition: str
    season: str


class TimelinePoint(TypedDict):
    i: int
    date: str
    pts: int
    rolling: float


class Ratings(TypedDict):
    win_pct: int | None
    ppg: int | None
    attack: int | None
    defence: int | None
    elo: int | None
    value: int | None


class Manager(TypedDict):
    slug: str
    name: str
    interim: bool
    start: str
    end: str | None
    games: int
    w: int
    d: int
    l: int
    win_pct: float | None
    ppg: float | None
    gf_pg: float | None
    ga_pg: float | None
    xg_diff_pg: float | None
    best_finish: int | None
    best_finish_season: str | None
    trophies: list[Trophy]
    elo_start: float | None
    elo_end: float | None
    net_spend_real: float | None
    places_vs_model: float | None
    model_seasons: int
    how_it_ended: str
    tagline: str
    bounce_first10_ppg: float | None
    bounce_rest_ppg: float | None
    cluster: str | None
    lineup: Lineup | None
    season_lineups: list[Lineup]
    best_signings: list[SigningCard]
    worst_signings: list[SigningCard]
    timeline: list[TimelinePoint]
    ratings: Ratings
    portrait: str | None
    credit: Credit | None


class ManagersData(TypedDict):
    generated: str
    managers: list[Manager]
    lineup_note: str


# ---------- finances -------------------------------------------------------------


class ResourceModelOut(TypedDict):
    resource: str
    resource_label: str
    intercept: float
    slope: float
    r2: float
    n: int
    first_season: str
    last_season: str


class ScatterPoint(TypedDict):
    season: int
    season_label: str
    team: str
    rel: float
    ppg: float
    pred_ppg: float
    residual: float
    position: int
    expected_position: float
    places_vs_model: float
    in_progress: bool


class ClubSummary(TypedDict):
    team: str
    display: str
    seasons: int
    mean_residual_ppg: float
    total_points_vs_model: float
    mean_places_vs_model: float


class NetSpendRow(TypedDict):
    team: str
    season: int
    season_label: str
    spend: float
    sales: float
    net_spend: float
    points: int | None
    net_spend_per_point: float | None


class UnitedMoneyRow(TypedDict):
    season: int
    season_label: str
    fy_end_year: int
    revenue: float | None
    wages: float | None
    wages_to_revenue: float | None
    wages_per_point: float | None
    interest_paid: float | None
    dividends_paid: float | None
    debt_issue_costs: float | None
    net_debt: float | None
    borrowings: float | None


class GlazerTotals(TypedDict):
    first_fy: int
    last_fy: int
    interest_paid: float
    dividends_paid: float
    debt_issue_costs: float
    latest_net_debt: float | None


class FinancesData(TypedDict):
    generated: str
    cpi_base: str
    model: ResourceModelOut
    points: list[ScatterPoint]
    club_summary: list[ClubSummary]
    net_spend: list[NetSpendRow]
    united_money: list[UnitedMoneyRow]
    glazer_totals: GlazerTotals | None


# ---------- simulate -------------------------------------------------------------


class SimTeam(TypedDict):
    team: str
    display: str
    actual_points: int | None
    actual_position: int | None
    played: int
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float
    mean_points: float
    p_title: float
    p_top4: float
    p_relegation: float
    exp_position: float
    attack: float
    defence: float
    market_xpts: float | None


class ConvergencePoint(TypedDict):
    n: int
    p_title: float
    p_top4: float


class HistBin(TypedDict):
    points: int
    p: float


class SimSeason(TypedDict):
    season: int
    label: str
    in_progress: bool
    matches_played: int
    home_adv: float
    rho: float
    n_sims: int
    teams: list[SimTeam]
    united_hist: list[HistBin]
    convergence: list[ConvergencePoint]


class SimulateData(TypedDict):
    generated: str
    seasons: list[SimSeason]


# ---------- scouting -------------------------------------------------------------


class SeriesPoint(TypedDict):
    date: str
    v: float


class EloSeries(TypedDict):
    team: str
    display: str
    points: list[SeriesPoint]


class Break(TypedDict):
    index: int
    date: str
    support: float


class Segment(TypedDict):
    start: str
    end: str
    mean: float


class ChangepointSeries(TypedDict):
    label: str
    series: list[SeriesPoint]
    breaks: list[Break]
    segments: list[Segment]


class BouncePoint(TypedDict):
    rel: int
    ppg: float
    n: int


class UnitedBounce(TypedDict):
    manager: str
    start: str
    curve: list[BouncePoint]


class ClusterPoint(TypedDict):
    team: str
    display: str
    manager: str
    start: str
    end: str | None
    x: float
    y: float
    cluster: str
    ppg: float
    net_spend_per_season: float
    avg_squad_age: float
    elo_change_per_season: float


class RtmPoint(TypedDict):
    team: str
    season: int
    deviation: float
    next_change: float


class ScoutingData(TypedDict):
    generated: str
    elo: list[EloSeries]
    elo_source: str
    changepoints: list[ChangepointSeries]
    penalties: list[float]
    bounce_league: list[BouncePoint]
    bounce_united: list[UnitedBounce]
    bounce_n_changes: int
    clusters: list[ClusterPoint]
    cluster_k: int
    silhouettes: dict[str, float]
    pca_explained: list[float]
    rtm_points: list[RtmPoint]
    rtm_league_slope: float
    rtm_united_slope: float


# ---------- transfers ------------------------------------------------------------


class TransfersData(TypedDict):
    generated: str
    threshold_gbp_real: float
    signings: list[SigningCard]
    clubs: list[str]


# ---------- methodology / sources -------------------------------------------------


class Source(TypedDict):
    name: str
    url: str
    used_for: str
    coverage: str
    status: Literal["ok", "partial", "unavailable"]


class ModelNote(TypedDict):
    name: str
    summary: str


class MethodologyData(TypedDict):
    generated: str
    sources: list[Source]
    models: list[ModelNote]
    assumptions: list[str]
    gaps_markdown: str
    credits: list[Credit]


class SourcesData(TypedDict):
    generated: str
    sources: list[Source]


EXPORTS: dict[str, type] = {
    "menu.json": MenuData,
    "managers.json": ManagersData,
    "finances.json": FinancesData,
    "simulate.json": SimulateData,
    "scouting.json": ScoutingData,
    "transfers.json": TransfersData,
    "methodology.json": MethodologyData,
    "sources.json": SourcesData,
}


# ---------- TypeScript generation ------------------------------------------------

def _ts_type(tp: object) -> str:
    origin = get_origin(tp)
    if tp is str:
        return "string"
    if tp in (int, float):
        return "number"
    if tp is bool:
        return "boolean"
    if tp is type(None):
        return "null"
    if origin in (Union, types.UnionType):
        return " | ".join(_ts_type(a) for a in get_args(tp))
    if origin is list:
        inner = _ts_type(get_args(tp)[0])
        return f"({inner})[]" if "|" in inner else f"{inner}[]"
    if origin is dict:
        return f"Record<string, {_ts_type(get_args(tp)[1])}>"
    if origin is Literal:
        return " | ".join(f'"{a}"' for a in get_args(tp))
    if isinstance(tp, type) and typing.is_typeddict(tp):
        return tp.__name__
    raise TypeError(f"Unsupported type in schema: {tp!r}")


def _collect(tp: object, seen: dict[str, type]) -> None:
    if isinstance(tp, type) and typing.is_typeddict(tp):
        if tp.__name__ in seen:
            return
        for field_type in get_type_hints(tp).values():
            _collect(field_type, seen)
        seen[tp.__name__] = tp
        return
    for arg in get_args(tp):
        _collect(arg, seen)


def typescript_definitions() -> str:
    seen: dict[str, type] = {}
    for root in EXPORTS.values():
        _collect(root, seen)
    lines = [
        "// AUTO-GENERATED by analysis/export.py from analysis/schema.py. Do not edit by hand.",
        "// Re-run the pipeline after changing the schema.",
        "",
    ]
    for name, td in seen.items():
        lines.append(f"export interface {name} {{")
        for field, ftype in get_type_hints(td).items():
            lines.append(f"  {field}: {_ts_type(ftype)};")
        lines.append("}")
        lines.append("")
    lines.append("export interface DataFiles {")
    for fname, td in EXPORTS.items():
        lines.append(f'  "{fname}": {td.__name__};')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def validate(obj: object, tp: object, path: str = "$") -> None:
    """Light runtime check that exported data matches the schema."""
    origin = get_origin(tp)
    if isinstance(tp, type) and typing.is_typeddict(tp):
        if not isinstance(obj, dict):
            raise TypeError(f"{path}: expected object for {tp.__name__}")
        hints = get_type_hints(tp)
        missing = set(hints) - set(obj)
        extra = set(obj) - set(hints)
        if missing or extra:
            raise TypeError(f"{path}: {tp.__name__} missing={sorted(missing)} extra={sorted(extra)}")
        for k, t in hints.items():
            validate(obj[k], t, f"{path}.{k}")
        return
    if origin in (Union, types.UnionType):
        errors = []
        for a in get_args(tp):
            try:
                validate(obj, a, path)
                return
            except TypeError as exc:
                errors.append(str(exc))
        raise TypeError(f"{path}: no union member matched ({'; '.join(errors[:2])})")
    if origin is list:
        if not isinstance(obj, list):
            raise TypeError(f"{path}: expected list")
        for i, v in enumerate(obj):
            validate(v, get_args(tp)[0], f"{path}[{i}]")
        return
    if origin is dict:
        if not isinstance(obj, dict):
            raise TypeError(f"{path}: expected dict")
        for k, v in obj.items():
            validate(v, get_args(tp)[1], f"{path}.{k}")
        return
    if origin is Literal:
        if obj not in get_args(tp):
            raise TypeError(f"{path}: {obj!r} not in {get_args(tp)}")
        return
    if tp is type(None):
        if obj is not None:
            raise TypeError(f"{path}: expected null")
        return
    if tp is float:
        if not isinstance(obj, (int, float)) or isinstance(obj, bool):
            raise TypeError(f"{path}: expected number, got {type(obj).__name__}")
        return
    if tp is int:
        if not isinstance(obj, int) or isinstance(obj, bool):
            raise TypeError(f"{path}: expected int, got {type(obj).__name__}")
        return
    if not isinstance(obj, tp):  # type: ignore[arg-type]
        raise TypeError(f"{path}: expected {tp}, got {type(obj).__name__}")
