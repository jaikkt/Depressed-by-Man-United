"use client";

import { useMemo, useState } from "react";
import { BarChart } from "@/components/charts/BarChart";
import { LineChart } from "@/components/charts/LineChart";
import { ScatterChart } from "@/components/charts/ScatterChart";
import { GameShell } from "@/components/ui/GameShell";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { NoData } from "@/components/ui/NoData";
import { Panel } from "@/components/ui/Panel";
import { StatBar } from "@/components/ui/StatBar";
import { TabBar } from "@/components/ui/TabBar";
import { useData } from "@/lib/data";
import type { FinancesData } from "@/lib/data-types";
import { money, pct, signed, TEAM_COLORS, teamName } from "@/lib/format";
import styles from "./screens.module.css";

type Tab = "model" | "rivals" | "glazer";
const UNITED = "manchester-united";

export function Finances() {
  const { data, error } = useData("finances.json");
  const tips = useData("menu.json").data?.tips;
  const [tab, setTab] = useState<Tab>("model");
  return (
    <GameShell title="Club Finances" kicker="Mode 03" prompts={[{ action: "prevTab", label: "Prev tab" }, { action: "nextTab", label: "Next tab" }, { action: "back", label: "Back" }]}>
      <TabBar value={tab} onChange={setTab} tabs={[{ id: "model", label: "Money Model" }, { id: "rivals", label: "Rivals" }, { id: "glazer", label: "Glazer Era" }]} />
      <div className={styles.body}>
        {error ? <NoData detail={error} /> : !data ? <LoadingScreen mode="CLUB FINANCES" tip={tips?.[3]} /> : tab === "model" ? <ModelTab d={data} /> : tab === "rivals" ? <RivalsTab d={data} /> : <GlazerTab d={data} />}
      </div>
    </GameShell>
  );
}

function ModelTab({ d }: { d: FinancesData }) {
  const united = d.points.filter((p) => p.team === UNITED);
  const finished = united.filter((p) => !p.in_progress);
  const avgPost = mean(finished.filter((p) => p.season >= 2013).map((p) => p.places_vs_model));
  return (
    <div className={styles.grid2}>
      <Panel title="Squad value vs points" kicker={`${d.model.first_season} – ${d.model.last_season}`}>
        <ScatterChart
          data={d.points.map((p) => ({
            key: `${p.season}-${p.team}`, x: p.rel, y: p.ppg, highlight: p.team === UNITED,
            label: `${teamName(p.team)} ${p.season_label}: ${p.ppg.toFixed(2)} PPG, ${p.rel.toFixed(2)}× avg value`,
          }))}
          xLog
          xLabel="Squad value ÷ league average (log scale)"
          yLabel="Points per game"
          line={(x) => d.model.intercept + d.model.slope * Math.log(x)}
          xFormat={(v) => `${v.toFixed(1)}×`}
          yFormat={(v) => v.toFixed(1)}
        />
        <p className={styles.note}>
          PPG = {d.model.intercept.toFixed(2)} + {d.model.slope.toFixed(2)} × ln(relative squad value). R² = {d.model.r2.toFixed(2)}, n = {d.model.n} club-seasons.
          Red diamonds are United. Resource measure: {d.model.resource_label}. No open wage-bill data covers every club, so this stands in for wages.
        </p>
      </Panel>
      <div className={styles.stack}>
        <Panel title="The verdict" tone="raised">
          <div className={styles.verdict}>
            <div>
              <span className={styles.verdictNum}>{signed(avgPost)}</span>
              <span className={styles.verdictText}>league places per season vs what United&apos;s squad value predicts, since 2013-14 (completed seasons)</span>
            </div>
          </div>
        </Panel>
        <Panel title="United vs the model" kicker="Places above (+) or below (−)">
          <BarChart
            data={united.map((p) => ({
              key: String(p.season), label: p.season_label.slice(2), value: p.places_vs_model,
              tooltip: `${p.season_label}: finished ${p.position}, model said ${p.expected_position.toFixed(1)}`,
              tone: p.in_progress ? "grey" : p.places_vs_model < 0 ? "red" : "white",
            }))}
            yLabel="Places vs model"
            yFormat={(v) => signed(v, 0)}
          />
          <p className={styles.note}>Grey bar: season in progress, will move.</p>
        </Panel>
      </div>
    </div>
  );
}

function RivalsTab({ d }: { d: FinancesData }) {
  const [era, setEra] = useState<"post" | "all">("post");
  const from = era === "post" ? 2013 : 0;
  const clubs = useMemo(() => {
    const byClub = new Map<string, { spend: number; pts: number; seasons: number }>();
    for (const r of d.net_spend) {
      if (r.season < from || r.points === null) continue;
      const c = byClub.get(r.team) ?? { spend: 0, pts: 0, seasons: 0 };
      c.spend += r.net_spend;
      c.pts += r.points;
      c.seasons += 1;
      byClub.set(r.team, c);
    }
    return [...byClub.entries()].map(([team, c]) => ({ team, ...c, perPoint: c.pts ? c.spend / c.pts : null })).sort((a, b) => (b.perPoint ?? 0) - (a.perPoint ?? 0));
  }, [d, from]);
  const maxPer = Math.max(...clubs.map((c) => Math.abs(c.perPoint ?? 0)), 1);
  return (
    <div className={styles.grid2}>
      <Panel title="Return on squad value" kicker="Big six, model residual">
        {d.club_summary.map((c) => (
          <StatBar key={c.team} label={c.display} value={`${signed(c.mean_places_vs_model)} places`} rating={50 + c.mean_places_vs_model * 15} sub={`${signed(c.mean_residual_ppg, 2)} PPG · ${c.seasons} seasons`} />
        ))}
        <p className={styles.note}>Average places per season above or below what each club&apos;s squad value predicts.</p>
      </Panel>
      <Panel
        title="Net spend per league point"
        kicker={era === "post" ? "Since 2013-14" : "Whole PL era"}
        right={
          <span className={styles.eraToggle}>
            <button type="button" data-nav="" className={era === "post" ? styles.on : ""} onClick={() => setEra("post")}>POST-SAF</button>
            <button type="button" data-nav="" className={era === "all" ? styles.on : ""} onClick={() => setEra("all")}>ALL</button>
          </span>
        }
      >
        {clubs.map((c) => (
          <div key={c.team} className={styles.spendRow}>
            <span className={styles.spendTeam} style={{ color: c.team === UNITED ? "var(--red)" : undefined }}>{teamName(c.team)}</span>
            <span className={styles.spendBar}><span style={{ width: `${(Math.abs(c.perPoint ?? 0) / maxPer) * 100}%`, background: TEAM_COLORS[c.team] ?? "var(--grey)" }} /></span>
            <span className={styles.spendVal}>{money(c.perPoint, 2)}</span>
            <span className={styles.spendSub}>{money(c.spend)} net · {c.pts} pts</span>
          </div>
        ))}
        <p className={styles.note}>Known transfer fees only, in today&apos;s money (UK CPI, base {d.cpi_base}). Rival wage bills are not openly available (see Data Gaps).</p>
      </Panel>
    </div>
  );
}

function GlazerTab({ d }: { d: FinancesData }) {
  if (!d.united_money.length || !d.glazer_totals) return <NoData detail="No SEC filings data available." />;
  const t = d.glazer_totals;
  return (
    <div className={styles.grid2}>
      <div className={styles.stack}>
        <Panel title="Money out to service the takeover" kicker={`FY${t.first_fy}–FY${t.last_fy}`} tone="raised">
          <div className={styles.bigRow}>
            <div><span className={styles.bigLabel}>Interest paid</span><span className={styles.bigGold}>{money(t.interest_paid)}</span></div>
            <div><span className={styles.bigLabel}>Dividends</span><span className={styles.big}>{money(t.dividends_paid)}</span></div>
            <div><span className={styles.bigLabel}>Net debt (latest)</span><span className={styles.big}>{money(t.latest_net_debt)}</span></div>
          </div>
          <p className={styles.note}>
            From Manchester United plc 20-F filings (SEC XBRL), in today&apos;s money. The leveraged buyout dates from 2005, but machine-readable filings
            only cover FY{t.first_fy} onward, so 2005–{t.first_fy - 1} is missing. These totals understate the full Glazer-era outflow.
          </p>
        </Panel>
        <Panel title="Outflows by year">
          <BarChart
            data={d.united_money.map((r) => ({
              key: String(r.fy_end_year), label: `FY${String(r.fy_end_year).slice(2)}`,
              value: (r.interest_paid ?? 0) + (r.dividends_paid ?? 0) + (r.debt_issue_costs ?? 0),
              tooltip: `FY${r.fy_end_year}: interest ${money(r.interest_paid)}, dividends ${money(r.dividends_paid)}`,
              tone: "red",
            }))}
            yLabel="Interest + dividends + debt fees"
            yFormat={(v) => money(v)}
            height={240}
          />
        </Panel>
      </div>
      <div className={styles.stack}>
        <Panel title="Net debt">
          <LineChart
            height={240}
            yLabel="Net debt"
            series={[{ id: "nd", label: "Net debt", color: "var(--red)", width: 3, points: d.united_money.filter((r) => r.net_debt !== null).map((r) => ({ x: r.fy_end_year, y: r.net_debt ?? 0 })) }]}
            yFormat={(v) => money(v)}
            xFormat={(v) => `FY${String(v).slice(2)}`}
          />
        </Panel>
        <Panel title="Wages to revenue" kicker="United only">
          {d.united_money.map((r) => (
            <StatBar key={r.fy_end_year} label={`FY${r.fy_end_year}`} value={pct(r.wages_to_revenue)} rating={r.wages_to_revenue === null ? null : r.wages_to_revenue * 100}
              sub={`wages ${money(r.wages)} · per point ${money(r.wages_per_point, 1)}`} />
          ))}
          <p className={styles.note}>Rivals&apos; wage ratios: NO DATA (not in any open source we could use).</p>
        </Panel>
      </div>
    </div>
  );
}

function mean(xs: number[]): number | null {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
}
