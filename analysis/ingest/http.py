"""Polite, cached HTTP fetching shared by every ingest module.

Why a single module: every scraper must obey the same rules (descriptive
User-Agent, a few seconds between requests, cache everything in data/raw/),
so the rules live in one place and cannot drift between sources.
"""
from __future__ import annotations

import hashlib
import os
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
USER_AGENT = (
    "DepressedByManUTD-research/0.1 (student data project; "
    "respects robots.txt; cached; 1 request every few seconds)"
)
MIN_DELAY_SECONDS = float(os.environ.get("DBMU_MIN_DELAY", "3.0"))

_last_request_at: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


def cache_path(url: str, subdir: str) -> Path:
    """Stable on-disk name for a URL, so re-runs never hit the network twice."""
    digest = hashlib.sha1(url.encode()).hexdigest()[:16]
    tail = Path(urlparse(url).path).name or "index"
    safe_tail = "".join(c if c.isalnum() or c in "._-" else "_" for c in tail)[:60]
    return RAW_DIR / subdir / f"{safe_tail}__{digest}"


def allowed_by_robots(url: str) -> bool:
    host = urlparse(url).scheme + "://" + urlparse(url).netloc
    if host not in _robots:
        parser = urllib.robotparser.RobotFileParser()
        try:
            resp = requests.get(host + "/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=30)
            parser.parse(resp.text.splitlines() if resp.ok else [])
        except requests.RequestException:
            # Unreachable robots.txt: treat as "no rules", the standard convention.
            parser.parse([])
        _robots[host] = parser
    return _robots[host].can_fetch(USER_AGENT, url)


def _wait_for_slot(host: str) -> None:
    # Rate limit per host: being polite to one site shouldn't slow another.
    elapsed = time.monotonic() - _last_request_at.get(host, 0.0)
    if elapsed < MIN_DELAY_SECONDS:
        time.sleep(MIN_DELAY_SECONDS - elapsed)
    _last_request_at[host] = time.monotonic()


def fetch(url: str, subdir: str, *, refresh: bool = False, timeout: int = 60, official_api: bool = False) -> bytes | None:
    """Return the body for `url`, from cache when possible.

    Returns None (rather than raising) on failure, because callers must record
    a data gap instead of crashing the whole pipeline.

    `official_api=True` is only for documented machine APIs whose operators
    invite programmatic use under their own policy (e.g. the MediaWiki API,
    which en.wikipedia's robots.txt blocks for *crawlers* under /w/ but whose
    API etiquette page asks for a descriptive User-Agent and modest request
    rates, both of which we follow). HTML pages always go through robots.txt.
    """
    path = cache_path(url, subdir)
    if path.exists() and not refresh:
        return path.read_bytes()
    if not official_api and not allowed_by_robots(url):
        print(f"[robots] disallowed: {url}")
        return None
    _wait_for_slot(urlparse(url).netloc)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    except requests.RequestException as exc:
        print(f"[http] {url}: {exc}")
        return None
    if resp.status_code != 200:
        print(f"[http] {url}: status {resp.status_code}")
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return resp.content


def fetch_text(url: str, subdir: str, **kwargs: object) -> str | None:
    body = fetch(url, subdir, **kwargs)  # type: ignore[arg-type]
    return None if body is None else body.decode("utf-8", errors="replace")
