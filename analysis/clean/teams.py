"""Canonical team identifiers.

Every source spells clubs differently ("Man United", "Manchester Utd",
"Man Utd", "ManUnited"...). Joining sources on raw names silently drops rows,
so everything is mapped to one slug before any merge.
"""
from __future__ import annotations

import re
import unicodedata

UNITED = "manchester-united"
COMPARISON = ["manchester-city", "liverpool", "arsenal", "chelsea", "tottenham"]
BIG_SIX = [UNITED, *COMPARISON]

# Keys are normalised (lowercase, alphanumerics only) so punctuation/spacing variants collapse.
_ALIASES: dict[str, str] = {
    "manunited": UNITED, "manutd": UNITED, "manchesterutd": UNITED, "manchesterunited": UNITED,
    "manchesterunitedfc": UNITED, "manunitedfc": UNITED,
    "mancity": "manchester-city", "manchestercity": "manchester-city", "manchestercityfc": "manchester-city",
    "liverpool": "liverpool", "liverpoolfc": "liverpool", "fcliverpool": "liverpool",
    "arsenal": "arsenal", "arsenalfc": "arsenal", "fcarsenal": "arsenal",
    "chelsea": "chelsea", "chelseafc": "chelsea", "fcchelsea": "chelsea",
    "tottenham": "tottenham", "tottenhamhotspur": "tottenham", "spurs": "tottenham", "tottenhamhotspurfc": "tottenham",
    "newcastle": "newcastle", "newcastleunited": "newcastle", "newcastleutd": "newcastle",
    "westham": "west-ham", "westhamunited": "west-ham", "westhamutd": "west-ham",
    "westbrom": "west-brom", "westbromwichalbion": "west-brom", "wba": "west-brom",
    "wolves": "wolves", "wolverhampton": "wolves", "wolverhamptonwanderers": "wolves",
    "nottmforest": "nottingham-forest", "nottinghamforest": "nottingham-forest", "nottingham": "nottingham-forest", "forest": "nottingham-forest",
    "sheffieldweds": "sheffield-wednesday", "sheffieldwednesday": "sheffield-wednesday", "sheffwed": "sheffield-wednesday",
    "sheffieldunited": "sheffield-united", "sheffieldutd": "sheffield-united", "sheffutd": "sheffield-united",
    "qpr": "qpr", "queensparkrangers": "qpr",
    "brighton": "brighton", "brightonhovealbion": "brighton", "brightonandhovealbion": "brighton",
    "leicester": "leicester", "leicestercity": "leicester",
    "leeds": "leeds", "leedsunited": "leeds", "leedsutd": "leeds",
    "astonvilla": "aston-villa", "villa": "aston-villa",
    "blackburn": "blackburn", "blackburnrovers": "blackburn",
    "bolton": "bolton", "boltonwanderers": "bolton",
    "wimbledon": "wimbledon", "wimbledonfc2004": "wimbledon", "wimbledonfc": "wimbledon",
    "coventry": "coventry", "coventrycity": "coventry",
    "norwich": "norwich", "norwichcity": "norwich",
    "ipswich": "ipswich", "ipswichtown": "ipswich",
    "oldham": "oldham", "oldhamathletic": "oldham",
    "swindon": "swindon", "swindontown": "swindon",
    "middlesbrough": "middlesbrough", "middlesboro": "middlesbrough", "middlesbroughfc": "middlesbrough",
    "derby": "derby", "derbycounty": "derby",
    "charlton": "charlton", "charltonathletic": "charlton",
    "birmingham": "birmingham", "birminghamcity": "birmingham",
    "wigan": "wigan", "wiganathletic": "wigan",
    "stoke": "stoke", "stokecity": "stoke",
    "hull": "hull", "hullcity": "hull",
    "cardiff": "cardiff", "cardiffcity": "cardiff",
    "swansea": "swansea", "swanseacity": "swansea",
    "huddersfield": "huddersfield", "huddersfieldtown": "huddersfield",
    "bournemouth": "bournemouth", "afcbournemouth": "bournemouth",
    "brentford": "brentford", "brentfordfc": "brentford",
    "luton": "luton", "lutontown": "luton",
    "burnley": "burnley", "burnleyfc": "burnley",
    "watford": "watford", "watfordfc": "watford",
    "southampton": "southampton", "southamptonfc": "southampton",
    "everton": "everton", "evertonfc": "everton",
    "fulham": "fulham", "fulhamfc": "fulham",
    "crystalpalace": "crystal-palace", "palace": "crystal-palace",
    "sunderland": "sunderland", "sunderlandafc": "sunderland",
    "portsmouth": "portsmouth", "portsmouthfc": "portsmouth",
    "reading": "reading", "readingfc": "reading",
    "blackpool": "blackpool", "blackpoolfc": "blackpool",
    "bradford": "bradford", "bradfordcity": "bradford",
    "barnsley": "barnsley", "barnsleyfc": "barnsley",
    "boltonwanderersfc": "bolton",
}


def _normalise(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_name.lower())


def canonical(name: str) -> str:
    """Map any source spelling to a slug. Unknown names fall back to a slug of
    the raw name so nothing is dropped, but tests pin every PL club we've seen."""
    key = _normalise(name)
    if key in _ALIASES:
        return _ALIASES[key]
    stripped = re.sub(r"(fc|afc)$", "", key)
    if stripped in _ALIASES:
        return _ALIASES[stripped]
    return re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()).strip("-")


DISPLAY: dict[str, str] = {
    UNITED: "Man United", "manchester-city": "Man City", "liverpool": "Liverpool",
    "arsenal": "Arsenal", "chelsea": "Chelsea", "tottenham": "Tottenham",
}
