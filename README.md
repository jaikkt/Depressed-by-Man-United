# DepressedByManUTD

How badly have Manchester United underperformed what their money should buy?
A data study (Python) plus a website that looks and plays like a 2015–19 console
football game menu (Next.js).

**Thesis:** United aren't bad in absolute terms. They're bad *relative to their
resources*. Every model is fitted on every Premier League club, so United are
judged by the same yardstick as everyone else.

> Unofficial fan analysis. Not affiliated with Manchester United or EA Sports.

---

## Run it locally

Requirements: Python 3.11+ (built with 3.12 from Homebrew) and Node 20+.

### 1. Website only (the JSON is already in `web/public/data/`)

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000. Press Enter at the title screen. Arrow keys move, Enter
selects, Esc goes back, Q/E switch tabs or managers. A gamepad works too.

Production build (static files in `web/out/`, which any static host can serve):

```bash
cd web
npm run build
npx serve out
```

### 2. Rebuild the data from scratch

```bash
# one-off setup (macOS: brew install python@3.12 if you don't have 3.11+)
python3.12 -m venv analysis/.venv
analysis/.venv/bin/pip install -r analysis/requirements.txt

# ingest: every download is cached in analysis/data/raw/, so re-runs are instant
analysis/.venv/bin/python -m analysis.ingest.results              # football-data.co.uk + engsoccerdata
analysis/.venv/bin/python -m analysis.ingest.cpi                  # ONS CPI
analysis/.venv/bin/python -m analysis.ingest.united_financials    # SEC EDGAR 20-F XBRL
analysis/.venv/bin/python -m analysis.ingest.transfermarkt        # values, transfers, coaches, minutes (~30 min first time)
analysis/.venv/bin/python -m analysis.ingest.transfermarkt_lineups  # ~1,300 match reports (~2 h first time)
analysis/.venv/bin/python -m analysis.scripts.fetch_manager_images  # Wikimedia Commons portraits

# models + JSON + TypeScript types + DATA_GAPS.md
analysis/.venv/bin/python -m analysis.export

# tests
analysis/.venv/bin/python -m pytest analysis/tests -q
```

The scrapers are deliberately slow: one request every 3 seconds per site (set
`DBMU_MIN_DELAY=5` to go slower), with a descriptive User-Agent, and robots.txt
checked before every HTML page.

---

## What's inside

```
analysis/
  ingest/        one module per source (all cached, rate-limited, robots-aware)
  clean/         team-name mapping, seasons, money (FX + CPI), league tables
  models/        wage_regression, dixon_coles, monte_carlo, elo, changepoint,
                 manager_bounce, manager_eras, clustering, transfer_roi
  scripts/       fetch_manager_images.py
  data/manual/   small hand-checked facts (United managers, trophies)
  schema.py      the JSON contract; generates web/lib/data-types.ts
  export.py      runs everything and writes web/public/data/*.json
  tests/         pytest, one file per model family
  DATA_GAPS.md   regenerated on every export: what's missing and why
web/
  app/           one route per screen
  components/ui/ the game UI kit (see /kit)
  components/charts/  custom D3 charts
```

### Screens

| Route | Mode |
|---|---|
| `/` | Title screen + tile hub + headline ticker |
| `/managers` | **Manager Eras**: portrait, attributes, most common XI on a pitch, signings, PPG timeline |
| `/finances` | Squad-value model, rival comparison, Glazer-era outflows |
| `/simulate` | Dixon-Coles + 10,000 Monte Carlo seasons, any season 1992-93 to now |
| `/scouting` | Elo history, change points, manager bounce, tenure clusters, regression to the mean |
| `/transfers` | Every big-six signing over £10m (real), sortable, with stat cards |
| `/methodology` | Settings (sounds, reduced motion), sources, models, data gaps, image credits |
| `/kit` | Every UI component in every state |

### Key method decisions (details on the Methodology screen)

- **Squad value instead of wages.** No open dataset has every PL club's wage bill,
  so the spending model uses Transfermarkt squad market value (2004-05 onward). Add
  `analysis/data/manual/club_wages.csv` (`season,team,wages_gbp`) and the same code
  fits the true wage model.
- **Our own Elo.** The ClubElo API was down (HTTP 502) during the build, so Elo is
  computed from results and warmed up on 1985–92 First Division games.
- **No xG.** Understat disallows crawlers and FBref returns 403. Bookmaker-odds
  expected points are shown instead, clearly labelled.
- **Real money.** Everything is in pounds at the latest UK CPI price level.
- **Never invented.** Missing values are `null` in JSON and show as NO DATA.

---

## Roadmap (not built yet)

- Live what-if sliders on Simulate Season, running a TypeScript port of the simulator in a Web Worker
- "Career: The Decline" scroll-story screen
- Accessibility pass (WCAG AA, screen-reader chart summaries) and Lighthouse performance tuning
- Mobile layout polish below 768px
- Vercel deployment
- Bayesian team-strength model and a compare-any-club mode
- Hand-transcribed club wage bills (published accounts) to replace the squad-value proxy
- United FY2012–15 figures from the HTML 20-F filings

## Credits

Data: football-data.co.uk, engsoccerdata (James Curley), Transfermarkt, SEC EDGAR,
ONS, ECB. Portraits: Wikimedia Commons contributors under CC licences (see
`web/public/managers/credits.json` and the Methodology screen).
