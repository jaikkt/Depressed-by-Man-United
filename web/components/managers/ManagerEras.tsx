"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { Pitch } from "@/components/charts/Pitch";
import { PpgTimeline } from "@/components/charts/PpgTimeline";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { GameShell } from "@/components/ui/GameShell";
import { Icon } from "@/components/ui/Icon";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { NoData } from "@/components/ui/NoData";
import { Panel } from "@/components/ui/Panel";
import { Portrait } from "@/components/ui/Portrait";
import { RadarHex } from "@/components/ui/RadarHex";
import { SigningCard } from "@/components/ui/SigningCard";
import { StatBar } from "@/components/ui/StatBar";
import { useData } from "@/lib/data";
import type { Manager, Ratings } from "@/lib/data-types";
import { money, num, ordinal, pct, shortDate, signed } from "@/lib/format";
import { useKey } from "@/lib/input";
import { useSettings } from "@/lib/settings";
import { ManagerStrip } from "./ManagerStrip";
import styles from "./ManagerEras.module.css";

const RADAR_KEYS: { key: keyof Ratings; label: string }[] = [
  { key: "win_pct", label: "Win %" },
  { key: "ppg", label: "PPG" },
  { key: "attack", label: "Attack" },
  { key: "defence", label: "Defence" },
  { key: "elo", label: "Elo" },
  { key: "value", label: "Value" },
];

export function ManagerEras() {
  const { data, error } = useData("managers.json");
  const tips = useData("menu.json").data?.tips;
  const [picked, setPicked] = useState<number | null>(null);
  const [lineupKey, setLineupKey] = useState<string>("tenure");
  const { sfx } = useSettings();

  const managers = useMemo(() => data?.managers ?? [], [data]);
  // Default to the current manager: the most recent era is the one people ask about.
  const index = picked ?? Math.max(0, managers.length - 1);
  const m: Manager | undefined = managers[index];

  const select = (i: number) => {
    setPicked(i);
    setLineupKey("tenure");
  };
  useKey(["q"], () => {
    if (index > 0) {
      sfx("move");
      select(index - 1);
    }
  });
  useKey(["e"], () => {
    if (index < managers.length - 1) {
      sfx("move");
      select(index + 1);
    }
  });

  const clubPpg = useMemo(() => {
    const games = managers.reduce((a, x) => a + x.games, 0);
    const pts = managers.reduce((a, x) => a + (x.ppg ?? 0) * x.games, 0);
    return games ? pts / games : 0;
  }, [managers]);
  const ferguson = managers.find((x) => x.slug === "ferguson");

  if (error) return <GameShell title="Manager Eras" kicker="Mode"><NoData detail={error} /></GameShell>;
  if (!data || !m) return <GameShell title="Manager Eras" kicker="Mode"><LoadingScreen mode="MANAGER ERAS" tip={tips?.[2]} /></GameShell>;

  const lineup = lineupKey === "tenure" ? m.lineup : m.season_lineups.find((l) => l.label === lineupKey) ?? null;
  const maxStarts = lineup ? Math.max(...lineup.xi.map((p) => p.starts), 1) : 1;
  const trophyCounts = m.trophies.reduce<Record<string, number>>((acc, t) => ({ ...acc, [t.competition]: (acc[t.competition] ?? 0) + 1 }), {});

  return (
    <GameShell
      title="Manager Eras"
      kicker="Mode 01"
      prompts={[{ action: "moveH", label: "Change manager" }, { action: "move", label: "Navigate" }, { action: "select", label: "Select" }, { action: "back", label: "Back" }]}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={m.slug}
          className={styles.layout}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.18, ease: [0.2, 0.9, 0.2, 1] }}
        >
          {/* ---- hero: portrait + name ---- */}
          <section className={styles.hero}>
            <Portrait name={m.name} src={m.portrait} credit={m.credit} />
            <div className={styles.heroText}>
              <div className={styles.badges}>
                {m.interim ? <Badge tone="white">Interim</Badge> : <Badge>Manager</Badge>}
                {m.cluster ? <Badge tone="outline">{m.cluster}</Badge> : null}
              </div>
              <h2 className={styles.name}>
                {m.name.split(" ").slice(0, -1).join(" ")}
                <span>{m.name.split(" ").slice(-1)[0]}</span>
              </h2>
              <p className={styles.dates}>
                {shortDate(m.start)} – {shortDate(m.end)} · {m.games} LEAGUE GAMES
              </p>
              <p className={styles.tagline}>{m.tagline}</p>
              <div className={styles.bigStats}>
                <div>
                  <span className={styles.bigLabel}>Places vs squad-value model</span>
                  <span className={`${styles.bigValue} ${styles.gold}`}>{m.places_vs_model === null ? "N/A" : signed(m.places_vs_model)}</span>
                  <span className={styles.bigSub}>{m.model_seasons ? `avg over ${m.model_seasons} season${m.model_seasons > 1 ? "s" : ""} (2004-05 on)` : "model starts 2004-05"}</span>
                </div>
                <div>
                  <span className={styles.bigLabel}>Points per game</span>
                  <span className={styles.bigValue}>{num(m.ppg)}</span>
                  <span className={styles.bigSub}>club PL-era avg {clubPpg.toFixed(2)}</span>
                </div>
              </div>
              <p className={styles.ended}><Icon name="whistle" size={18} /> {m.how_it_ended}</p>
            </div>
          </section>

          {/* ---- right: attributes ---- */}
          <aside className={styles.side}>
            <Panel title="Attributes" kicker="League only">
              <WdlBar w={m.w} d={m.d} l={m.l} />
              <StatBar label="Win rate" value={pct(m.win_pct)} rating={m.ratings.win_pct} />
              <StatBar label="Points per game" value={num(m.ppg)} rating={m.ratings.ppg} />
              <StatBar label="Goals for / game" value={num(m.gf_pg)} rating={m.ratings.attack} />
              <StatBar label="Goals against / game" value={num(m.ga_pg)} rating={m.ratings.defence} />
              <StatBar label="xG diff / game" value="--" rating={m.xg_diff_pg} sub="no xG source" />
              <StatBar label="Elo start → end" value={m.elo_start === null ? "--" : `${Math.round(m.elo_start)} → ${Math.round(m.elo_end ?? 0)}`} rating={m.ratings.elo} />
              <StatBar label="Net spend" value={money(m.net_spend_real)} sub="today's £" />
              <StatBar label="Best league finish" value={m.best_finish ? `${ordinal(m.best_finish)}` : "--"} sub={m.best_finish_season ?? "under half a season"} />
              <StatBar label="New-manager bounce" value={m.bounce_first10_ppg === null ? "--" : `${num(m.bounce_first10_ppg)} → ${num(m.bounce_rest_ppg)}`} sub="PPG first 10 → rest" />
              <div className={styles.radar}>
                <RadarHex
                  size={230}
                  axes={RADAR_KEYS.map((k) => ({ label: k.label, value: m.ratings[k.key] }))}
                  compare={ferguson && ferguson.slug !== m.slug ? RADAR_KEYS.map((k) => ferguson.ratings[k.key]) : undefined}
                />
                {ferguson && ferguson.slug !== m.slug ? <span className={styles.radarKey}>Dashed: Ferguson (PL era)</span> : null}
              </div>
            </Panel>
            <Panel title="Trophy Cabinet" tone="raised">
              {m.trophies.length === 0 ? (
                <p className={styles.emptyCabinet}>Empty shelf.</p>
              ) : (
                <ul className={styles.cabinet}>
                  {Object.entries(trophyCounts).map(([comp, n]) => (
                    <li key={comp}>
                      <Icon name="trophy" size={26} />
                      <span className={styles.trophyN}>{n}</span>
                      <span className={styles.trophyName}>{comp}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </aside>

          {/* ---- left: pitch ---- */}
          <section className={styles.pitchCol}>
            <Panel title="Most common XI" kicker={lineup ? `${lineup.formation}${lineup.formation_inferred ? " · inferred" : ""}` : ""}>
              <div className={styles.seasonToggles}>
                <Button variant={lineupKey === "tenure" ? "primary" : "secondary"} active={lineupKey === "tenure"} onClick={() => setLineupKey("tenure")}>Tenure</Button>
                {m.season_lineups.map((l) => (
                  <Button key={l.label} variant="secondary" active={lineupKey === l.label} onClick={() => setLineupKey(l.label)}>
                    {l.label}
                  </Button>
                ))}
              </div>
              {lineup && lineup.xi.length ? (
                <>
                  <Pitch xi={lineup.xi} maxStarts={maxStarts} />
                  <p className={styles.lineupMeta}>
                    {lineup.formation} used in {lineup.formation_matches} of {lineup.matches_with_lineup} games with a recorded XI ·
                    coverage {pct(lineup.coverage)}
                  </p>
                  {lineup.formation_inferred ? (
                    <p className={styles.lineupMeta}>INFERRED: these reports list players by position group only, so the formation comes from the group counts and left-right placement is approximate.</p>
                  ) : null}
                  {lineup.exact_xi ? (
                    <p className={styles.lineupMeta}>Most repeated exact XI: {lineup.exact_xi.times} times.</p>
                  ) : (
                    <p className={styles.lineupMeta}>No exact XI was ever repeated.</p>
                  )}
                </>
              ) : (
                <NoData detail="No recorded line-ups for this period." />
              )}
            </Panel>
          </section>

          {/* ---- bottom: signings + timeline ---- */}
          <section className={styles.bottom}>
            <Panel title="PPG timeline" kicker="10-game rolling">
              {m.timeline.length ? <PpgTimeline points={m.timeline} reference={clubPpg} /> : <NoData compact />}
            </Panel>
            <div className={styles.cards}>
              {m.best_signings.slice(0, 1).map((c) => <SigningCard key={c.player_id + c.season} card={c} tone="best" />)}
              {m.worst_signings.slice(0, 1).map((c) => <SigningCard key={c.player_id + c.season} card={c} tone="worst" />)}
              {m.best_signings.length + m.worst_signings.length === 0 ? <NoData detail="No £10m+ league signings credited to this manager." /> : null}
            </div>
          </section>
        </motion.div>
      </AnimatePresence>
      <div className={styles.stripDock}>
        <ManagerStrip managers={managers} index={index} onSelect={select} />
      </div>
    </GameShell>
  );
}

function WdlBar({ w, d, l }: { w: number; d: number; l: number }) {
  const n = Math.max(1, w + d + l);
  return (
    <div className={styles.wdl} aria-label={`${w} wins, ${d} draws, ${l} losses`}>
      <div className={styles.wdlBar}>
        <span style={{ width: `${(w / n) * 100}%` }} className={styles.win} />
        <span style={{ width: `${(d / n) * 100}%` }} className={styles.draw} />
        <span style={{ width: `${(l / n) * 100}%` }} className={styles.loss} />
      </div>
      <div className={styles.wdlNums}>
        <span>W {w}</span>
        <span>D {d}</span>
        <span>L {l}</span>
      </div>
    </div>
  );
}
