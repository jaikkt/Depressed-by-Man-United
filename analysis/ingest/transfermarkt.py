"""Transfermarkt: squad values/ages, transfers, manager histories, player minutes.

Pages used (all allowed by transfermarkt.co.uk/robots.txt, all cached):
  * league overview per season  -> every PL club's TM id, squad size, average
    age and total squad market value (values exist from ~2004/05 onward)
  * league transfers per season -> every PL club's arrivals/departures + fees
  * club coach history          -> manager start/end dates for every PL club
  * club league stats per season (big six only) -> minutes, goals, assists

Fees and market values are shown in euros. They are converted to pounds with
the ECB annual average GBP/EUR rate for the season's start year (see fx.py).

Run:  analysis/.venv/bin/python -m analysis.ingest.transfermarkt
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from analysis.clean.seasons import FIRST_PL_SEASON, current_season_start
from analysis.clean.teams import BIG_SIX, canonical
from analysis.ingest.http import fetch_text

BASE = "https://www.transfermarkt.co.uk"
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


def parse_money_eur(text: str) -> float | None:
    """'€12.85m' -> 12_850_000. Loan fees, 'free transfer', '-', '?' -> None
    (unknown) or 0 (free) so that unknown is never confused with free."""
    t = text.strip().lower()
    if not t or t in {"-", "?"} or "loan" in t or "end of loan" in t:
        return None
    if "free" in t:
        return 0.0
    m = re.search(r"€\s*([\d.,]+)\s*(bn|m|k|th\.)?", t)
    if not m:
        return None
    value = float(m.group(1).replace(",", ""))
    scale = {"bn": 1e9, "m": 1e6, "k": 1e3, "th.": 1e3}.get(m.group(2) or "", 1.0)
    return value * scale


def is_loan(text: str) -> bool:
    return "loan" in text.lower()


def parse_int(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


# ---------- league overview ----------------------------------------------------

def league_overview_url(season: int) -> str:
    return f"{BASE}/premier-league/startseite/wettbewerb/GB1/saison_id/{season}"


def parse_league_overview(html: str, season: int) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.items")
    rows = []
    for tr in table.select("tbody > tr") if table else []:
        link = tr.select_one("td.hauptlink a[href*='/verein/']")
        tds = tr.find_all("td", recursive=False)
        if link is None or len(tds) < 7:
            continue
        name = link.get("title") or link.get_text(strip=True)
        tm_id = re.search(r"/verein/(\d+)", link["href"]).group(1)  # type: ignore[union-attr]
        cells = [td.get_text(" ", strip=True) for td in tds]
        rows.append({
            "season": season,
            "team": canonical(re.sub(r"\s*\(-\s*\d{4}\)", "", str(name))),
            "tm_name": name,
            "tm_id": tm_id,
            "squad_size": parse_int(cells[2]),
            "avg_age": float(cells[3]) if re.fullmatch(r"[\d.]+", cells[3]) else None,
            "squad_value_eur": parse_money_eur(cells[-1]),
        })
    return pd.DataFrame(rows)


# ---------- transfers ----------------------------------------------------------

def league_transfers_url(season: int) -> str:
    return f"{BASE}/premier-league/transfers/wettbewerb/GB1/saison_id/{season}"


def parse_league_transfers(html: str, season: int) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for box in soup.select("div.box"):
        club_link = box.select_one("h2 a[href*='/verein/']")
        if club_link is None:
            continue
        team = canonical(re.sub(r"\s*\(-\s*\d{4}\)", "", club_link.get("title") or club_link.get_text(strip=True)))
        for table in box.select("table"):
            head = [th.get_text(strip=True) for th in table.select("thead th")]
            if not head or head[0] not in {"In", "Out"}:
                continue
            direction = "in" if head[0] == "In" else "out"
            for tr in table.select("tbody tr"):
                tds = tr.find_all("td", recursive=False)
                player = tr.select_one("a[href*='/profil/spieler/']")
                if player is None or len(tds) < 8:
                    continue
                fee_text = tds[-1].get_text(" ", strip=True)
                other = tds[-2].get_text(" ", strip=True)
                age_text = tds[1].get_text(strip=True)
                rows.append({
                    "season": season,
                    "team": team,
                    "direction": direction,
                    "player_id": player["href"].split("/")[-1],
                    "player_slug": player["href"].split("/")[1],
                    "player": player.get("title") or player.get_text(strip=True),
                    "age": int(age_text) if age_text.isdigit() else None,
                    "position": tds[3].get_text(strip=True),
                    "other_club": other,
                    "fee_text": fee_text,
                    "fee_eur": parse_money_eur(fee_text),
                    "is_loan": is_loan(fee_text),
                })
    return pd.DataFrame(rows)


# ---------- coach history ------------------------------------------------------

def coach_history_url(tm_id: str) -> str:
    return f"{BASE}/x/mitarbeiterhistorie/verein/{tm_id}"


def parse_coach_history(html: str, team: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.items")
    rows = []
    for tr in table.select("tbody > tr") if table else []:
        tds = tr.find_all("td", recursive=False)
        link = tr.select_one("td.hauptlink a[href*='/trainer/']")
        if link is None or len(tds) < 6:
            continue
        rows.append({
            "team": team,
            "manager": link.get("title") or link.get_text(strip=True),
            "manager_tm_id": link["href"].split("/")[-1],
            "start": pd.to_datetime(tds[2].get_text(strip=True), dayfirst=True, errors="coerce"),
            "end": pd.to_datetime(tds[3].get_text(strip=True), dayfirst=True, errors="coerce"),
        })
    return pd.DataFrame(rows)


# ---------- player league stats (big six) --------------------------------------

def squad_stats_url(tm_id: str, season: int) -> str:
    return f"{BASE}/x/leistungsdaten/verein/{tm_id}/reldata/GB1%26{season}/plus/1"


def parse_squad_stats(html: str, team: str, season: int) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.items")
    rows = []
    for tr in table.select("tbody > tr") if table else []:
        tds = tr.find_all("td", recursive=False)
        player = tr.select_one("a[href*='/profil/spieler/']")
        if player is None or len(tds) < 15:
            continue
        cells = [td.get_text(" ", strip=True) for td in tds]
        apps = parse_int(cells[5]) if "Not used" not in cells[5] else 0
        rows.append({
            "season": season,
            "team": team,
            "player_id": player["href"].split("/")[-1],
            "player": player.get("title") or player.get_text(strip=True),
            "age": parse_int(cells[2]) or None,
            "apps": apps,
            "goals": parse_int(cells[6]),
            "assists": parse_int(cells[7]),
            "subs_on": parse_int(cells[11]),
            "minutes": parse_int(cells[14]),
        })
    return pd.DataFrame(rows)


# ---------- orchestration ------------------------------------------------------

def run(last_season: int) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    overview, transfers = [], []
    for season in range(FIRST_PL_SEASON, last_season + 1):
        html = fetch_text(league_overview_url(season), "transfermarkt")
        if html:
            overview.append(parse_league_overview(html, season))
        html = fetch_text(league_transfers_url(season), "transfermarkt")
        if html:
            transfers.append(parse_league_transfers(html, season))
        print(f"[tm] season {season} overview+transfers done")
    ov = pd.concat(overview, ignore_index=True)
    ov.to_parquet(PROCESSED / "tm_league_overview.parquet", index=False)
    pd.concat(transfers, ignore_index=True).to_parquet(PROCESSED / "tm_transfers.parquet", index=False)

    clubs = ov.drop_duplicates("team")[["team", "tm_id"]]
    coaches = []
    for team, tm_id in clubs.itertuples(index=False):
        html = fetch_text(coach_history_url(tm_id), "transfermarkt")
        if html:
            coaches.append(parse_coach_history(html, team))
    pd.concat(coaches, ignore_index=True).to_parquet(PROCESSED / "tm_coaches.parquet", index=False)
    print(f"[tm] coach histories for {len(coaches)} clubs")

    stats = []
    for team in BIG_SIX:
        tm_ids = ov.loc[ov["team"] == team, "tm_id"]
        if tm_ids.empty:
            continue
        tm_id = tm_ids.iloc[0]
        for season in sorted(ov.loc[ov["team"] == team, "season"]):
            html = fetch_text(squad_stats_url(tm_id, season), "transfermarkt")
            if html:
                stats.append(parse_squad_stats(html, team, season))
        print(f"[tm] squad stats {team} done")
    pd.concat(stats, ignore_index=True).to_parquet(PROCESSED / "tm_squad_stats.parquet", index=False)


if __name__ == "__main__":
    run(current_season_start())
