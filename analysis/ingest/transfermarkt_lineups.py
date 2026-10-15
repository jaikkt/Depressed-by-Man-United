"""United league line-ups and formations from Transfermarkt match reports.

Why Transfermarkt: FBref blocks automated access (HTTP 403) and Understat
disallows all crawling in robots.txt, while Transfermarkt's robots.txt allows
it and its match reports carry the formation *and* each starter's pitch
coordinates, which lets us define position slots without guessing.

Run:  analysis/.venv/bin/python -m analysis.ingest.transfermarkt_lineups
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, Tag

from analysis.ingest.http import fetch_text

BASE = "https://www.transfermarkt.co.uk"
UNITED_TM_ID = "985"
FIRST_SEASON = 1992  # Transfermarkt labels seasons by start year: 1992 = 1992/93
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


@dataclass
class FixtureRow:
    season: int
    matchday: int
    date: str  # dd/mm/yyyy as shown on the page
    venue: str  # "H" or "A"
    opponent: str
    result: str  # "2:1" from the page, United's perspective is NOT guaranteed
    report_id: str


@dataclass
class StarterRow:
    report_id: str
    season: int
    formation: str | None
    player_id: str
    player_slug: str
    short_name: str
    shirt: str | None
    top: float  # % from top of the pitch graphic (own goal at the bottom)
    left: float  # % from left
    manager: str | None
    inferred: bool  # True = old list-style report: formation inferred, coordinates are a template


def fixtures_url(season: int) -> str:
    return f"{BASE}/manchester-united/spielplan/verein/{UNITED_TM_ID}/saison_id/{season}"


def report_url(report_id: str) -> str:
    return f"{BASE}/spielbericht/index/spielbericht/{report_id}"


def parse_fixtures(html: str, season: int) -> list[FixtureRow]:
    """Premier League rows only; cup games would distort league formations."""
    soup = BeautifulSoup(html, "lxml")
    out: list[FixtureRow] = []
    for box in soup.select("div.box"):
        head = box.select_one("h2")
        if not head or head.get_text(strip=True) != "Premier League":
            continue
        for tr in box.select("table tbody tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            link = next((a["href"] for a in tr.select("a") if "spielbericht/index" in a.get("href", "")), None)
            if len(cells) < 10 or link is None:
                continue
            result = cells[-1]
            if not re.fullmatch(r"\d+:\d+", result):
                continue  # unplayed or postponed
            out.append(
                FixtureRow(
                    season=season,
                    matchday=int(cells[0]) if cells[0].isdigit() else -1,
                    date=cells[1].split(" ")[-1],
                    venue=cells[3],
                    opponent=re.sub(r"\s*\(\d+\.\)", "", cells[6]).strip(),
                    result=result,
                    report_id=str(link).rstrip("/").split("/")[-1],
                )
            )
    return out


def _united_lineup_block(soup: BeautifulSoup) -> Tag | None:
    """United's half of the Line-Ups box. The home side's div carries the
    class 'aufstellung-box' but the away side's doesn't, so we find the block
    by United's team link instead of by class."""
    for box in soup.select("div.box"):
        head = box.select_one("h2")
        if not head or "Line-Ups" not in head.get_text():
            continue
        for block in box.find_all("div", recursive=False):
            link = block.select_one("a.sb-vereinslink")
            if link and f"/verein/{UNITED_TM_ID}/" in link.get("href", ""):
                return block
    return None


def _percent(style: str, key: str) -> float:
    match = re.search(rf"{key}:\s*([\d.]+)%", style)
    return float(match.group(1)) if match else float("nan")


# Template rows (top %) for list-style reports, matching the pitch template's scale.
GROUP_TOP = {"Goalkeeper": 80.0, "Defenders": 62.0, "Midfield": 38.0, "Midfielders": 38.0, "Forwards": 5.0, "Strikers": 5.0}


def _spread(n: int) -> list[float]:
    """Evenly spread n players across the width (left-edge %, 0-75 scale)."""
    if n == 1:
        return [40.0]
    return [7.5 + i * (65.0 / (n - 1)) for i in range(n)]


def _parse_list_style(block: Tag, report_id: str, season: int, manager: str | None) -> list[StarterRow]:
    """Older reports list starters by position group instead of drawing a pitch.
    Formation = counts of defenders-midfielders-forwards (an inference, flagged)."""
    groups: list[tuple[str, list[Tag]]] = []
    for tr in block.select("table tr"):
        label = tr.select_one("td b")
        links = tr.select("a[href*='/profil/spieler/']")
        if label is None or not links:
            continue
        groups.append((label.get_text(strip=True), links))
    outfield = [len(links) for g, links in groups if g != "Goalkeeper"]
    formation = "-".join(str(n) for n in outfield) if outfield else None
    rows: list[StarterRow] = []
    for group, links in groups:
        top = GROUP_TOP.get(group, 40.0)
        for left, link in zip(_spread(len(links)), links):
            href = str(link["href"])
            rows.append(StarterRow(report_id=report_id, season=season, formation=formation, player_id=href.split("/")[-1],
                                   player_slug=href.split("/")[1], short_name=link.get_text(strip=True), shirt=None,
                                   top=top, left=round(left, 1), manager=manager, inferred=True))
    return rows


def parse_report(html: str, report_id: str, season: int) -> list[StarterRow]:
    soup = BeautifulSoup(html, "lxml")
    block = _united_lineup_block(soup)
    if block is None:
        return []
    manager_link = block.select_one("a[href*='/profil/trainer/']")
    manager = manager_link.get_text(strip=True) if manager_link else None
    containers = block.select("div.formation-player-container")
    if not containers:
        return _parse_list_style(block, report_id, season, manager)
    subtitle = block.select_one(".formation-subtitle")
    formation = None
    if subtitle:
        text = subtitle.get_text(" ", strip=True).replace("Starting Line-up:", "").strip()
        formation = text or None
    rows: list[StarterRow] = []
    for cont in containers:
        link = cont.select_one("a[href*='/profil/spieler/']")
        if link is None:
            continue
        href = link["href"]
        shirt_el = cont.select_one(".tm-shirt-number")
        style = cont.get("style", "")
        rows.append(
            StarterRow(
                report_id=report_id,
                season=season,
                formation=formation,
                player_id=str(href).split("/")[-1],
                player_slug=str(href).split("/")[1],
                short_name=link.get_text(strip=True),
                shirt=shirt_el.get_text(strip=True) if shirt_el else None,
                top=_percent(str(style), "top"),
                left=_percent(str(style), "left"),
                manager=manager,
                inferred=False,
            )
        )
    return rows


def run(last_season: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixtures: list[FixtureRow] = []
    starters: list[StarterRow] = []
    for season in range(FIRST_SEASON, last_season + 1):
        html = fetch_text(fixtures_url(season), "transfermarkt")
        if html is None:
            print(f"[lineups] no fixtures page for {season}")
            continue
        season_fixtures = parse_fixtures(html, season)
        fixtures.extend(season_fixtures)
        for fx in season_fixtures:
            report = fetch_text(report_url(fx.report_id), "transfermarkt")
            if report is None:
                continue
            starters.extend(parse_report(report, fx.report_id, season))
        print(f"[lineups] {season}: {len(season_fixtures)} league matches")
    fx_df = pd.DataFrame([asdict(f) for f in fixtures])
    st_df = pd.DataFrame([asdict(s) for s in starters])
    PROCESSED.mkdir(parents=True, exist_ok=True)
    fx_df.to_parquet(PROCESSED / "united_tm_fixtures.parquet", index=False)
    st_df.to_parquet(PROCESSED / "united_starters.parquet", index=False)
    return fx_df, st_df


if __name__ == "__main__":
    from analysis.clean.seasons import current_season_start

    run(current_season_start())
