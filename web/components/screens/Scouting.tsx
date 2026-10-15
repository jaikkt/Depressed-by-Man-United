"use client";

import { useMemo, useState } from "react";
import { LineChart, type LineSeries } from "@/components/charts/LineChart";
import { ScatterChart } from "@/components/charts/ScatterChart";
import { Button } from "@/components/ui/Button";
import { GameShell } from "@/components/ui/GameShell";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { NoData } from "@/components/ui/NoData";
import { Panel } from "@/components/ui/Panel";
import { TabBar } from "@/components/ui/TabBar";
import { useData } from "@/lib/data";
import type { ScoutingData } from "@/lib/data-types";
import { money, num, signed, TEAM_COLORS, teamName } from "@/lib/format";
import styles from "./screens.module.css";

type Tab = "elo" | "breaks" | "bounce" | "clusters" | "rtm";
const UNITED = "manchester-united";
const yearFmt = (v: number | Date) => (v instanceof Date ? String(v.getFullYear()) : String(v));
const monthFmt = (v: number | Date) => (v instanceof Date ? v.toLocaleDateString("en-GB", { month: "short", year: "numeric" }).toUpperCase() : String(v));

export function Scouting() {
  const { data, error } = useData("scouting.json");
  const tips = useData("menu.json").data?.tips;
  const [tab, setTab] = useState<Tab>("elo");
  return (
    <GameShell title="Scouting Report" kicker="Mode 04" prompts={[{ action: "prevTab", label: "Prev report" }, { action: "nextTab", label: "Next report" }, { action: "back", label: "Back" }]}>
      <TabBar
        value={tab}
        onChange={setTab}
        tabs={[{ id: "elo", label: "Elo History" }, { id: "breaks", label: "Change Points" }, { id: "bounce", label: "Manager Bounce" }, { id: "clusters", label: "Tenure Types" }, { id: "rtm", label: "Regression" }]}
      />
      <div className={styles.body}>
        {error ? <NoData detail={error} /> : !data ? <LoadingScreen mode="SCOUTING REPORT" tip={tips?.[1]} /> : (
          <>
            {tab === "elo" && <EloTab d={data} />}
            {tab === "breaks" && <BreaksTab d={data} />}
            {tab === "bounce" && <BounceTab d={data} />}
            {tab === "clusters" && <ClustersTab d={data} />}
            {tab === "rtm" && <RtmTab d={data} />}
          </>
        )}
      </div>
    </GameShell>
  );
}

function EloTab({ d }: { d: ScoutingData }) {
  const series: LineSeries[] = d.elo.map((s) => ({
    id: s.team, label: s.display, color: TEAM_COLORS[s.team] ?? "var(--grey)", width: s.team === UNITED ? 3.5 : 1.5,
    dash: s.team === UNITED ? undefined : s.team === "manchester-city" ? "1 0" : "5 3",
    points: s.points.map((p) => ({ x: new Date(p.date), y: p.v })),
  }));
  // Draw United last so it sits on top.
  series.sort((a, b) => Number(a.id === UNITED) - Number(b.id === UNITED));
  const breaks = d.changepoints.find((c) => c.label === "ELO RATING")?.breaks ?? [];
  return (
    <Panel title="Elo rating, big six" kicker={d.elo_source}>
      <LineChart series={series} yLabel="Elo" height={420} xFormat={yearFmt} yFormat={(v) => v.toFixed(0)}
        markers={breaks.filter((b) => b.support >= 0.5).map((b) => ({ x: new Date(b.date), label: b.date.slice(0, 7), strength: b.support }))} />
      <p className={styles.note}>Gold lines: robust change points in United&apos;s Elo (see Change Points). Ratings are computed from PL results only, warmed up on 1985–92 First Division games.</p>
    </Panel>
  );
}

function BreaksTab({ d }: { d: ScoutingData }) {
  return (
    <div className={styles.stack}>
      {d.changepoints.map((c) => (
        <Panel key={c.label} title={c.label} kicker="PELT change points">
          <LineChart
            height={300}
            yLabel={c.label.includes("PPG") ? "PPG" : "Elo"}
            series={[{ id: c.label, label: "United", color: "var(--red)", width: 2.5, points: c.series.map((p) => ({ x: new Date(p.date), y: p.v })) }]}
            markers={c.breaks.map((b) => ({ x: new Date(b.date), label: monthFmt(new Date(b.date)), strength: b.support }))}
            segments={c.segments.map((s) => ({ x0: new Date(s.start), x1: new Date(s.end), y: s.mean }))}
            xFormat={yearFmt}
            yFormat={(v) => (c.label.includes("PPG") ? v.toFixed(1) : v.toFixed(0))}
            legend={false}
          />
          <p className={styles.note}>
            Run at penalties {d.penalties.join(", ")}. Solid gold: the break appears at half or more of the penalties. Faint dashed: it appears at fewer (not trusted).
            White bars: mean level between robust breaks.
          </p>
        </Panel>
      ))}
    </div>
  );
}

function BounceTab({ d }: { d: ScoutingData }) {
  const [pick, setPick] = useState<string>("all");
  const united = d.bounce_united.filter((b) => pick === "all" || b.manager + b.start === pick);
  const series: LineSeries[] = [
    { id: "league", label: `League baseline (${d.bounce_n_changes} changes)`, color: "var(--white)", width: 3, points: d.bounce_league.map((p) => ({ x: p.rel, y: p.ppg })) },
    ...united.map((b, i) => ({
      id: b.manager + b.start, label: `${b.manager.split(" ").slice(-1)[0]} ${b.start.slice(0, 4)}`,
      color: pick === "all" ? `hsl(4, ${70 - i * 4}%, ${45 + i * 4}%)` : "var(--red)", width: pick === "all" ? 1.5 : 3,
      points: b.curve.map((p) => ({ x: p.rel, y: p.ppg })),
    })),
  ];
  return (
    <Panel
      title="New-manager bounce"
      kicker="Game 0 = first league game in charge"
    >
      <div className={styles.filters}>
        <Button variant="secondary" active={pick === "all"} onClick={() => setPick("all")}>All</Button>
        {d.bounce_united.map((b) => (
          <Button key={b.manager + b.start} variant="secondary" active={pick === b.manager + b.start} onClick={() => setPick(b.manager + b.start)}>
            {b.manager.split(" ").slice(-1)[0]} {b.start.slice(2, 4)}
          </Button>
        ))}
      </div>
      <LineChart series={series} height={400} yLabel="PPG (5-game smooth)" xLabel="Games relative to change" yDomain={[0, 3]} xFormat={(v) => String(v)} yFormat={(v) => v.toFixed(1)}
        markers={[{ x: 0, label: "NEW MANAGER", strength: 1 }]} />
      <p className={styles.note}>
        The league baseline averages every other PL club&apos;s managerial change (spells of 10+ league games). The typical &quot;bounce&quot; is mostly a
        return from the low point that got the old manager sacked.
      </p>
    </Panel>
  );
}

function ClustersTab({ d }: { d: ScoutingData }) {
  const groups = useMemo(() => [...new Set(d.clusters.map((c) => c.cluster))], [d]);
  const palette = ["#F4F1EA", "#8A8A90", "#4B4B51", "#C9C4BA", "#5f5f66", "#2f2f34"];
  const colors = Object.fromEntries(groups.map((g, i) => [g, palette[i % palette.length]]));
  const bestK = d.silhouettes[String(d.cluster_k)];
  return (
    <div className={styles.grid2}>
      <Panel title="Tenure types" kicker={`k-means, k = ${d.cluster_k}`}>
        <ScatterChart
          data={d.clusters.map((c) => ({
            key: c.team + c.start + c.manager, x: c.x, y: c.y, group: c.cluster, highlight: c.team === UNITED,
            label: `${c.manager} (${c.display}, ${c.start.slice(0, 4)}): ${c.cluster}`,
          }))}
          groupColors={colors}
          xLabel={`PC1 (${(d.pca_explained[0] * 100).toFixed(0)}% of variance)`}
          yLabel={`PC2 (${(d.pca_explained[1] * 100).toFixed(0)}%)`}
          xFormat={(v) => v.toFixed(1)}
          yFormat={(v) => v.toFixed(1)}
          zeroLines
          height={420}
        />
        <div className={styles.filters}>
          {groups.map((g) => <span key={g} style={{ display: "inline-flex", gap: 6, alignItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 13 }}><span style={{ width: 12, height: 12, background: colors[g] }} />{g}</span>)}
        </div>
        <p className={styles.note}>
          Silhouette score {num(bestK, 2)} (k chosen from {Object.keys(d.silhouettes).join(", ")}). Below 0.5 means the groups overlap, so read the labels loosely.
          Red diamonds are United tenures. xG difference was planned as a feature but no xG source was available.
        </p>
      </Panel>
      <Panel title="United tenures">
        <table className={styles.table}>
          <thead><tr><th>Manager</th><th>Type</th><th>PPG</th><th>Net £/season</th><th>Elo/season</th></tr></thead>
          <tbody>
            {d.clusters.filter((c) => c.team === UNITED).map((c) => (
              <tr key={c.start + c.manager}>
                <td className={styles.teamCell}>{c.manager}</td>
                <td>{c.cluster}</td>
                <td>{num(c.ppg)}</td>
                <td>{money(c.net_spend_per_season)}</td>
                <td>{signed(c.elo_change_per_season, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}

function RtmTab({ d }: { d: ScoutingData }) {
  return (
    <div className={styles.grid2}>
      <Panel title="What happens after a good season?" kicker="All PL clubs">
        <ScatterChart
          data={d.rtm_points.map((p) => ({
            key: p.team + p.season, x: p.deviation, y: p.next_change, highlight: p.team === UNITED,
            label: `${teamName(p.team)} ${p.season}: ${signed(p.deviation, 2)} vs trend, then ${signed(p.next_change, 2)}`,
          }))}
          xLabel="PPG vs previous 3-season average"
          yLabel="Change in PPG next season"
          line={(x) => d.rtm_league_slope * x}
          xFormat={(v) => signed(v, 1)}
          yFormat={(v) => signed(v, 1)}
          zeroLines
          height={420}
        />
      </Panel>
      <Panel title="The numbers" tone="raised">
        <div className={styles.bigRow}>
          <div><span className={styles.bigLabel}>League slope</span><span className={styles.big}>{num(d.rtm_league_slope)}</span></div>
          <div><span className={styles.bigLabel}>United slope</span><span className={styles.bigGold}>{num(d.rtm_united_slope)}</span></div>
        </div>
        <p className={styles.note}>
          A slope of −1 would mean every point above trend is given back the next season; 0 would mean gains stick. Across the league, about{" "}
          {Math.round(Math.abs(d.rtm_league_slope) * 100)}% of an above-trend season is given back the next year. For United it is about {Math.round(Math.abs(d.rtm_united_slope) * 100)}%.
          The dashed line is the league fit.
        </p>
      </Panel>
    </div>
  );
}
