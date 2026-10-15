"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { Gauge } from "@/components/charts/Gauge";
import { Histogram } from "@/components/charts/Histogram";
import { LineChart } from "@/components/charts/LineChart";
import { Button } from "@/components/ui/Button";
import { GameShell } from "@/components/ui/GameShell";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { NoData } from "@/components/ui/NoData";
import { Panel } from "@/components/ui/Panel";
import { useData } from "@/lib/data";
import type { SimSeason } from "@/lib/data-types";
import { num, ordinal, pct } from "@/lib/format";
import { useKey } from "@/lib/input";
import { useSettings } from "@/lib/settings";
import styles from "./screens.module.css";

const UNITED = "manchester-united";
type Phase = "pick" | "kickoff" | "running" | "done";

export function Simulate() {
  const { data, error } = useData("simulate.json");
  const tips = useData("menu.json").data?.tips;
  const seasons = useMemo(() => (data?.seasons ?? []).filter((s) => s.teams.some((t) => t.team === UNITED)), [data]);
  const [idx, setIdx] = useState<number | null>(null);
  const [phase, setPhase] = useState<Phase>("pick");
  const [progress, setProgress] = useState(0);
  const { reducedMotion, sfx } = useSettings();
  const raf = useRef(0);

  const i = idx ?? Math.max(0, seasons.length - 1);
  const season: SimSeason | undefined = seasons[i];

  const step = (delta: number) => {
    const next = Math.max(0, Math.min(seasons.length - 1, i + delta));
    if (next !== i) {
      sfx("move");
      setIdx(next);
      setPhase("pick");
      setProgress(0);
    }
  };
  useKey(["q"], () => step(-1));
  useKey(["e"], () => step(1));

  const run = () => {
    if (reducedMotion) {
      setProgress(1);
      setPhase("done");
      return;
    }
    setPhase("kickoff");
    setProgress(0);
  };

  useEffect(() => {
    if (phase === "kickoff") {
      const t = setTimeout(() => setPhase("running"), 900);
      return () => clearTimeout(t);
    }
    if (phase === "running") {
      // The 10,000 simulations were run by the pipeline; this counter replays
      // them visually so the distribution "fills in" like a sim in progress.
      const start = performance.now();
      const tick = (now: number) => {
        const p = Math.min(1, (now - start) / 1600);
        setProgress(p);
        if (p < 1) raf.current = requestAnimationFrame(tick);
        else setPhase("done");
      };
      raf.current = requestAnimationFrame(tick);
      return () => cancelAnimationFrame(raf.current);
    }
  }, [phase]);

  if (error) return <GameShell title="Simulate Season" kicker="Mode 02"><NoData detail={error} /></GameShell>;
  if (!data || !season) return <GameShell title="Simulate Season" kicker="Mode 02"><LoadingScreen mode="SIMULATE SEASON" tip={tips?.[0]} /></GameShell>;

  const u = season.teams.find((t) => t.team === UNITED);
  const shown = phase === "done" || phase === "running";
  const ease = 1 - Math.pow(1 - progress, 3);

  return (
    <GameShell
      title="Simulate Season"
      kicker="Mode 02"
      prompts={[{ action: "prevTab", label: "Prev season" }, { action: "nextTab", label: "Next season" }, { action: "select", label: "Kick off" }, { action: "back", label: "Back" }]}
    >
      <AnimatePresence>
        {phase === "kickoff" ? (
          <motion.div className={styles.kickoff} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
            <motion.span className={styles.kickoffSub} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>{season.label}</motion.span>
            <motion.span className={styles.kickoffText} initial={{ scale: 1.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.25, ease: [0.2, 0.9, 0.2, 1] }}>KICK-OFF</motion.span>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className={styles.body}>
        <div className={styles.simTop}>
          <div className={styles.seasonPicker}>
            <Button variant="secondary" glyph="prevTab" onClick={() => step(-1)} disabled={i === 0} ariaLabel="Previous season">Prev</Button>
            <span className={styles.seasonLabel}>{season.label}</span>
            <Button variant="secondary" glyph="nextTab" onClick={() => step(1)} disabled={i === seasons.length - 1} ariaLabel="Next season">Next</Button>
          </div>
          <Button size="lg" glyph="select" onClick={run} navDefault>{phase === "done" ? "Re-run" : "Kick off"}</Button>
          <div>
            <div className={styles.counter}>{Math.round(ease * season.n_sims).toLocaleString("en-GB")}</div>
            <div className={styles.counterLabel}>SEASONS SIMULATED</div>
          </div>
        </div>

        {!u ? <NoData /> : (
          <div className={styles.grid2}>
            <div className={styles.stack}>
              <Panel title="United: simulated points" kicker={season.in_progress ? `In progress · ${season.matches_played} games played` : "Full season replayed"}>
                {shown ? (
                  <Histogram bins={season.united_hist} actual={season.in_progress ? null : u.actual_points} p5={u.p5} p95={u.p95} revealed={ease} />
                ) : (
                  <NoData label="PRESS KICK OFF" detail="Replays the season 10,000 times with each team's fitted Dixon-Coles strengths." />
                )}
                <p className={styles.note}>
                  {season.in_progress
                    ? `Current points ${u.actual_points} from ${u.played} games. Remaining fixtures simulated; strengths fitted on this season plus last season with time decay. Early-season estimates are noisy.`
                    : `Actual: ${u.actual_points} pts, finished ${ordinal(u.actual_position)}. Median simulated: ${Math.round(u.p50)} pts. Expected position ${num(u.exp_position, 1)}.`}
                  {u.market_xpts !== null ? ` Bookmaker-implied expected points: ${num(u.market_xpts, 1)}.` : ""}
                </p>
              </Panel>
              <Panel title="Probabilities">
                <div className={styles.gauges}>
                  <Gauge value={shown ? u.p_title * ease : 0} label="Title" tone="gold" />
                  <Gauge value={shown ? u.p_top4 * ease : 0} label="Top four" tone="white" />
                  <Gauge value={shown ? u.p_relegation * ease : 0} label="Relegation" />
                </div>
              </Panel>
              <Panel title="Convergence check" kicker="P(top four) vs number of runs">
                {season.convergence.length ? (
                  <LineChart
                    height={200}
                    yLabel="P(top 4)"
                    xLabel="Simulations"
                    legend={false}
                    series={[
                      { id: "t4", label: "Top 4", color: "var(--white)", width: 3, points: season.convergence.map((c) => ({ x: c.n, y: c.p_top4 })) },
                      { id: "t1", label: "Title", color: "var(--gold)", width: 2, points: season.convergence.map((c) => ({ x: c.n, y: c.p_title })) },
                    ]}
                    yFormat={(v) => pct(v)}
                    xFormat={(v) => Number(v).toLocaleString("en-GB")}
                  />
                ) : <NoData compact />}
                <p className={styles.note}>White: top four. Gold: title. Flat lines well before 10,000 runs mean the estimates have converged.</p>
              </Panel>
            </div>
            <Panel title="Simulated table" kicker={`Home adv ×${num(season.home_adv, 2)} · ρ ${num(season.rho, 2)}`}>
              <table className={styles.table}>
                <thead>
                  <tr><th>Team</th><th>Exp pos</th><th>Med pts</th><th>5–95%</th><th>Title</th><th>Top 4</th><th>Actual</th></tr>
                </thead>
                <tbody>
                  {season.teams.map((t) => (
                    <tr key={t.team} className={t.team === UNITED ? styles.hl : ""}>
                      <td className={styles.teamCell}>{t.display}</td>
                      <td>{num(t.exp_position, 1)}</td>
                      <td>{Math.round(t.p50)}</td>
                      <td>{Math.round(t.p5)}–{Math.round(t.p95)}</td>
                      <td>{pct(t.p_title, t.p_title < 0.1 ? 1 : 0)}</td>
                      <td>{pct(t.p_top4)}</td>
                      <td>{t.actual_points} ({ordinal(t.actual_position)})</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          </div>
        )}
      </div>
    </GameShell>
  );
}
