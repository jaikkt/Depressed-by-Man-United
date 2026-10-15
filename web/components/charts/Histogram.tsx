"use client";

import * as d3 from "d3";
import type { HistBin } from "@/lib/data-types";
import { AxisBottom, AxisLeft } from "./axes";
import styles from "./ChartTooltip.module.css";
import { useWidth } from "./useWidth";

/** Simulated points distribution with the actual total marked in gold. */
export function Histogram({ bins, actual, p5, p95, height = 300, revealed = 1 }: {
  bins: HistBin[];
  actual: number | null;
  p5: number;
  p95: number;
  height?: number;
  revealed?: number; // 0..1, animates bars growing during the "simulation"
}) {
  const { ref, width } = useWidth<HTMLDivElement>();
  const m = { t: 30, r: 16, b: 44, l: 50 };
  const xs = bins.map((b) => b.points);
  const lo = Math.min(d3.min(xs) ?? 0, actual ?? Infinity) - 2;
  const hi = Math.max(d3.max(xs) ?? 0, actual ?? -Infinity) + 2;
  const x = d3.scaleLinear().domain([lo, hi]).range([m.l, width - m.r]);
  const y = d3.scaleLinear().domain([0, (d3.max(bins, (b) => b.p) ?? 0.05) * 1.1]).range([height - m.b, m.t]);
  const bw = Math.max(1, x(1) - x(0) - 1);
  return (
    <div ref={ref} className={styles.wrap}>
      <svg width={width} height={height} role="img" aria-label={`Simulated points distribution; 90% of simulations between ${p5} and ${p95}; actual ${actual ?? "unknown"}`}>
        <rect x={x(p5)} y={m.t} width={Math.max(0, x(p95) - x(p5))} height={height - m.b - m.t} fill="rgba(244,241,234,0.05)" />
        <AxisLeft scale={y} x={m.l} ticks={4} grid={width - m.l - m.r} format={(v) => `${(v * 100).toFixed(0)}%`} label="Share of sims" />
        <AxisBottom scale={x} y={height - m.b} label="Points" />
        {bins.map((b) => (
          <rect key={b.points} x={x(b.points) - bw / 2} y={y(b.p * revealed)} width={bw} height={height - m.b - y(b.p * revealed)}
            fill={actual !== null && b.points === actual ? "var(--gold)" : "var(--red)"} />
        ))}
        {actual !== null && revealed >= 1 ? (
          <g transform={`translate(${x(actual)} 0)`}>
            <line y1={m.t - 6} y2={height - m.b} stroke="var(--gold)" strokeWidth="3" />
            <rect x="-40" y={m.t - 26} width="80" height="20" fill="var(--gold)" />
            <text y={m.t - 11} textAnchor="middle" fontFamily="var(--font-display)" fontWeight="800" fontSize="13" fill="var(--black)">ACTUAL {actual}</text>
          </g>
        ) : null}
      </svg>
      <p className={styles.summary}>Shaded band: middle 90% of simulated seasons ({Math.round(p5)}–{Math.round(p95)} pts).</p>
    </div>
  );
}
