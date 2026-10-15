# DepressedByManUTD: website

Next.js (App Router, static export) + TypeScript + D3 + Framer Motion + CSS Modules.
See the project README one level up for how to run everything.

- `app/`: one route per screen (`/`, `/managers`, `/finances`, `/simulate`, `/scouting`, `/transfers`, `/methodology`, `/kit`)
- `components/ui/`: the game UI kit (Button, Tile, Panel, TabBar, PromptBar, StatBar, RatingNumber, RadarHex, Ticker, LoadingScreen, …)
- `components/charts/`: custom D3 charts (React renders the SVG; D3 does scales and paths)
- `lib/data-types.ts`: **generated** by `analysis/export.py`; do not edit by hand
- `public/data/`: JSON written by the Python pipeline
- `public/managers/`: free-licence portraits + `credits.json`
