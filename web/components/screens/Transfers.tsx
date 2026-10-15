"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { GameShell } from "@/components/ui/GameShell";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { NoData } from "@/components/ui/NoData";
import { Panel } from "@/components/ui/Panel";
import { SigningCard } from "@/components/ui/SigningCard";
import { useData } from "@/lib/data";
import type { SigningCard as Card } from "@/lib/data-types";
import { money, num, pct, teamName } from "@/lib/format";
import { useKey } from "@/lib/input";
import { useSettings } from "@/lib/settings";
import styles from "./screens.module.css";

type SortKey = "fee_gbp_real" | "cost_per_1000_min" | "league_minutes" | "net_cost_gbp_real" | "season" | "value_rating";
const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "season", label: "Season" },
  { key: "fee_gbp_real", label: "Fee" },
  { key: "league_minutes", label: "Lg mins" },
  { key: "net_cost_gbp_real", label: "Net cost" },
  { key: "cost_per_1000_min", label: "£ / 1k mins" },
  { key: "value_rating", label: "Value" },
];

export function Transfers() {
  const { data, error } = useData("transfers.json");
  const tips = useData("menu.json").data?.tips;
  const [club, setClub] = useState("manchester-united");
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: "cost_per_1000_min", desc: true });
  const [open, setOpen] = useState<Card | null>(null);
  const { sfx } = useSettings();

  useKey(["Escape"], (e) => {
    if (open) {
      e.preventDefault(); // close the card instead of leaving the screen
      sfx("back");
      setOpen(null);
    }
  }, open !== null);

  // Signings from the newest season have barely played: their cost per minute is
  // meaningless, so they're labelled NEW and treated as missing when sorting.
  const latest = useMemo(() => Math.max(0, ...(data?.signings ?? []).map((s) => s.season)), [data]);
  const isNew = (s: Card) => s.season === latest;
  const rows = useMemo(() => {
    const list = (data?.signings ?? []).filter((s) => club === "all" || s.team === club);
    const val = (s: Card) => (s.season === latest && (sort.key === "cost_per_1000_min" || sort.key === "value_rating") ? null : s[sort.key]);
    return [...list].sort((a, b) => {
      const va = val(a);
      const vb = val(b);
      if (va === null) return 1; // missing values always sink to the bottom
      if (vb === null) return -1;
      return sort.desc ? vb - va : va - vb;
    });
  }, [data, club, sort, latest]);

  if (error) return <GameShell title="Transfer Market" kicker="Mode 05"><NoData detail={error} /></GameShell>;
  if (!data) return <GameShell title="Transfer Market" kicker="Mode 05"><LoadingScreen mode="TRANSFER MARKET" tip={tips?.[4]} /></GameShell>;

  return (
    <GameShell title="Transfer Market" kicker="Mode 05" prompts={[{ action: "move", label: "Browse" }, { action: "select", label: "Player card" }, { action: "back", label: open ? "Close card" : "Back" }]}>
      <div className={styles.body}>
        <Panel title={`Signings over ${money(data.threshold_gbp_real)}`} kicker="Today's money · league minutes only" right={<span>{rows.length} players</span>}>
          <div className={styles.filters}>
            <span className={styles.counterLabel}>CLUB</span>
            {["all", ...data.clubs].map((c) => (
              <Button key={c} variant="secondary" active={club === c} onClick={() => setClub(c)} navDefault={c === "manchester-united"}>
                {c === "all" ? "All six" : teamName(c)}
              </Button>
            ))}
          </div>
          {rows.length === 0 ? <NoData detail="No signings data. Run the Transfermarkt ingest." /> : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Player</th>
                  <th>Club</th>
                  {COLUMNS.map((c) => (
                    <th key={c.key}>
                      <button type="button" className={styles.sortBtn} data-nav="" onClick={() => setSort((s) => ({ key: c.key, desc: s.key === c.key ? !s.desc : true }))}>
                        {c.label}{sort.key === c.key ? (sort.desc ? " ▼" : " ▲") : ""}
                      </button>
                    </th>
                  ))}
                  <th>Starter seasons</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr
                    key={s.team + s.player_id + s.season}
                    className={styles.tRow}
                    tabIndex={0}
                    data-nav=""
                    onClick={() => { sfx("select"); setOpen(s); }}
                    onKeyDown={(e) => { if (e.key === "Enter") { sfx("select"); setOpen(s); } }}
                  >
                    <td className={styles.teamCell}>{s.player}</td>
                    <td>{teamName(s.team)}</td>
                    <td>{s.season_label}</td>
                    <td>{money(s.fee_gbp_real)}</td>
                    <td>{s.league_minutes.toLocaleString("en-GB")}</td>
                    <td>{money(s.net_cost_gbp_real)}</td>
                    <td style={{ color: s.cost_per_1000_min === null || isNew(s) ? "var(--grey)" : undefined }}>{isNew(s) ? "NEW" : s.cost_per_1000_min === null ? "NO MINS" : money(s.cost_per_1000_min, 1)}</td>
                    <td>{isNew(s) ? "--" : s.value_rating}</td>
                    <td>{pct(s.regular_share)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className={styles.note}>
            Net cost = fee minus resale fee (players still at the club have no resale yet). Value rating = percentile of cost per 1,000 league minutes across all
            big-six signings (99 = best value). Unknown fees and loans are excluded. G+A per 90 shown on cards needs at least 450 minutes. Avg G+A/90 on this list:{" "}
            {num(avg(rows.map((r) => r.ga_per90)))}.
          </p>
        </Panel>
      </div>
      <AnimatePresence>
        {open ? (
          <motion.div className={styles.modalBack} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(null)} role="dialog" aria-modal="true" aria-label={`${open.player} card`}>
            <motion.div className={styles.modalCard} initial={{ y: 30, scale: 0.96 }} animate={{ y: 0, scale: 1 }} exit={{ y: 20, opacity: 0 }} transition={{ duration: 0.18 }} onClick={(e) => e.stopPropagation()}>
              <SigningCard card={open} tone={open.value_rating >= 70 ? "best" : open.value_rating <= 30 ? "worst" : undefined} />
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </GameShell>
  );
}

function avg(xs: (number | null)[]): number | null {
  const v = xs.filter((x): x is number => x !== null);
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
}
