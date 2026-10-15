"""Download freely licensed manager portraits from Wikimedia Commons.

For each manager we take the lead image of their English Wikipedia article
(via the pageimages API), then read its licence from Commons' extmetadata.
Only CC BY, CC BY-SA, CC0 and public-domain images are accepted; anything
else is skipped and the site shows the stylised initials fallback instead.
Attribution (title, author, licence, source URL) goes to credits.json, which
the site shows under each portrait and on the Methodology screen.

Run:  analysis/.venv/bin/python -m analysis.scripts.fetch_manager_images
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

from analysis.ingest.http import fetch

OUT_DIR = Path(__file__).resolve().parents[2] / "web" / "public" / "managers"
WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# person slug -> English Wikipedia article title
PEOPLE: dict[str, tuple[str, str]] = {
    "ferguson": ("Alex Ferguson", "Alex Ferguson"),
    "moyes": ("David Moyes", "David Moyes"),
    "giggs": ("Ryan Giggs", "Ryan Giggs"),
    "van-gaal": ("Louis van Gaal", "Louis van Gaal"),
    "mourinho": ("José Mourinho", "José Mourinho"),
    "solskjaer": ("Ole Gunnar Solskjaer", "Ole Gunnar Solskjær"),
    "carrick": ("Michael Carrick", "Michael Carrick"),
    "rangnick": ("Ralf Rangnick", "Ralf Rangnick"),
    "ten-hag": ("Erik ten Hag", "Erik ten Hag"),
    "van-nistelrooy": ("Ruud van Nistelrooy", "Ruud van Nistelrooy"),
    "amorim": ("Ruben Amorim", "Rúben Amorim"),
    "fletcher": ("Darren Fletcher", "Darren Fletcher"),
}

FREE_LICENCE = re.compile(r"^(cc[ -]by(-sa)?( \d\.\d)?.*|cc0.*|public domain.*|pd.*)$", re.IGNORECASE)


def is_free(licence: str) -> bool:
    lic = licence.strip()
    if re.search(r"\bnc\b|\bnd\b|non-?commercial|no ?deriv", lic, re.IGNORECASE):
        return False
    return bool(FREE_LICENCE.match(lic))


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def lead_image(article: str) -> str | None:
    url = f"{WIKI_API}?action=query&format=json&prop=pageimages&piprop=name&titles={quote(article)}"
    raw = fetch(url, "wikimedia", official_api=True)
    if raw is None:
        return None
    pages = json.loads(raw)["query"]["pages"]
    page = next(iter(pages.values()))
    return page.get("pageimage")


def image_info(filename: str) -> dict[str, str] | None:
    url = (f"{COMMONS_API}?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata"
           f"&iiurlwidth=600&titles={quote('File:' + filename)}")
    raw = fetch(url, "wikimedia", official_api=True)
    if raw is None:
        return None
    pages = json.loads(raw)["query"]["pages"]
    page = next(iter(pages.values()))
    if "imageinfo" not in page:
        return None  # file hosted locally on en.wikipedia (often non-free)
    info = page["imageinfo"][0]
    meta = info.get("extmetadata", {})
    return {
        "thumb": info.get("thumburl", info["url"]),
        "source_url": info.get("descriptionurl", ""),
        "license": meta.get("LicenseShortName", {}).get("value", ""),
        "author": strip_html(meta.get("Artist", {}).get("value", "Unknown")),
        "title": filename,
    }


def commons_search(name: str, surname: str) -> list[str]:
    """Fallback when the Wikipedia lead image isn't on Commons: search Commons
    files and keep only those whose title contains the surname, so we never
    pick a photo of somebody else."""
    url = (f"{COMMONS_API}?action=query&format=json&list=search&srnamespace=6&srlimit=10"
           f"&srsearch={quote(name)}")
    raw = fetch(url, "wikimedia", official_api=True)
    if raw is None:
        return []
    hits = [h["title"].removeprefix("File:") for h in json.loads(raw)["query"]["search"]]
    plain = lambda t: t.lower().replace("ú", "u")  # noqa: E731
    return [h for h in hits if plain(surname) in plain(h) and h.lower().endswith((".jpg", ".jpeg", ".png"))]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    credits: list[dict[str, str]] = []
    for slug, (name, article) in PEOPLE.items():
        filename = lead_image(article)
        info = image_info(filename) if filename else None
        if info is None or not is_free(info["license"]):
            for candidate in commons_search(article, article.split()[-1]):
                alt = image_info(candidate)
                if alt is not None and is_free(alt["license"]):
                    info = alt
                    break
        if info is None or not is_free(info["license"]):
            print(f"[portraits] {name}: no free image ({info['license'] if info else 'none'})")
            continue
        body = fetch(info["thumb"], "wikimedia")
        if body is None:
            continue
        ext = ".png" if info["thumb"].lower().endswith(".png") else ".jpg"
        (OUT_DIR / f"{slug}{ext}").write_bytes(body)
        credits.append({"slug": slug, "name": name, "file": f"/managers/{slug}{ext}", "title": info["title"],
                        "author": info["author"], "license": info["license"], "source_url": info["source_url"]})
        print(f"[portraits] {name}: {info['license']} by {info['author']}")
    (OUT_DIR / "credits.json").write_text(json.dumps(credits, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
