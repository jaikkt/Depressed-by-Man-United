"use client";

import * as d3 from "d3";
import { useState } from "react";
import { AxisLeft } from "./axes";
import styles from "./ChartTooltip.module.css";
import { useWidth } from "./useWidth";

export interface BarDatum {
  key: string;
  label: string; // x tick label
  value: number | null;
  tooltip: string;
  tone?: "red" | "white" | "grey" | "gold";
}

/** Diverging vertical bars around zero, skewed like the rest of the UI. */
export function BarChart({ data, yLabel, height = 300, yFormat, tickEvery = 1 }: {
  data: BarDatum[];
  yLabel: string;
  height?: number;
  yFormat?: (v: number) => string;
  tickEvery?: number;
}) {
  const { ref, width } = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<{ d: BarDatum; x: number; y: number } | null>(null);
  const m = { t: 18, r: 10, b: 46, l: 54 };
  const values = data.map((d) => d.value ?? 0);
  const lo = Math.min(0, d3.min(values) ?? 0);
  const hi = Math.max(0, d3.max(values) ?? 0);
  const y = d3.scaleLinear().domain([lo, hi]).range([height - m.b, m.t]).nice();
  const x = d3.scaleBand<string>().domain(data.map((d) => d.key)).range([m.l, width - m.r]).padding(0.25);
  const colors = { red: "var(--red)", white: "var(--white)", grey: "var(--grey-dark)", gold: "var(--gold)" };
  return (
    <div ref={ref} className={styles.wrap}>
      <svg width={width} height={height} role="img" aria-label={`${yLabel} by ${data.length} categories`}>
        <AxisLeft scale={y} x={m.l} grid={width - m.l - m.r} format={yFormat} label={yLabel} />
        <line x1={m.l} x2={width - m.r} y1={y(0)} y2={y(0)} stroke="var(--grey)" />
        {data.map((d, i) => {
          const bx = x(d.key) ?? 0;
          if (d.value === null) {
            return <text key={d.key} x={bx + x.bandwidth() / 2} y={y(0) - 6} textAnchor="middle" fontSize="9" fill="var(--grey-dark)" fontFamily="var(--font-display)">N/A</text>;
          }
          const y0 = y(Math.max(0, d.value));
          const h = Math.abs(y(d.value) - y(0));
          return (
            <g key={d.key}>
              <rect
                x={bx} y={y0} width={x.bandwidth()} height={Math.max(1, h)}
                fill={colors[d.tone ?? (d.value < 0 ? "red" : "white")]}
                transform={`skewX(-8) translate(${(y0 + h) * Math.tan((8 * Math.PI) / 180)} 0)`}
                onMouseEnter={() => setHover({ d, x: bx + x.bandwidth() / 2, y: y0 })}
                onMouseLeave={() => setHover(null)}
              />
              {i % tickEvery === 0 ? (
                <text x={bx + x.bandwidth() / 2} y={height - m.b + 16} textAnchor="end" transform={`rotate(-45 ${bx + x.bandwidth() / 2} ${height - m.b + 16})`} fontSize="11" fill="var(--grey)" fontFamily="var(--font-display)" fontWeight="600">
                  {d.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      {hover ? <span className={styles.tip} style={{ left: hover.x, top: hover.y }}>{hover.d.tooltip}</span> : null}
    </div>
  );
}
