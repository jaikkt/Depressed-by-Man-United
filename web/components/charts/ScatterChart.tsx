"use client";

import * as d3 from "d3";
import { useState } from "react";
import { AxisBottom, AxisLeft } from "./axes";
import styles from "./ChartTooltip.module.css";
import { useWidth } from "./useWidth";

export interface ScatterDatum {
  key: string;
  x: number;
  y: number;
  label: string;
  group?: string;
  highlight?: boolean;
}

/** Generic scatter: grey field, highlighted points in red on top, optional fitted line. */
export function ScatterChart({ data, xLabel, yLabel, height = 360, line, xFormat, yFormat, groupColors, xLog = false, zeroLines = false }: {
  data: ScatterDatum[];
  xLabel: string;
  yLabel: string;
  height?: number;
  line?: (x: number) => number;
  xFormat?: (v: number) => string;
  yFormat?: (v: number) => string;
  groupColors?: Record<string, string>;
  xLog?: boolean;
  zeroLines?: boolean;
}) {
  const { ref, width } = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<ScatterDatum | null>(null);
  const m = { t: 20, r: 18, b: 44, l: 50 };
  const xs = data.map((d) => d.x);
  const ys = data.map((d) => d.y);
  const xExt = d3.extent(xs) as [number, number];
  const yExt = d3.extent(ys) as [number, number];
  const x = (xLog ? d3.scaleLog() : d3.scaleLinear()).domain(xLog ? xExt : padExt(xExt)).range([m.l, width - m.r]).nice();
  const y = d3.scaleLinear().domain(padExt(yExt)).range([height - m.b, m.t]).nice();
  const sorted = [...data].sort((a, b) => Number(a.highlight ?? false) - Number(b.highlight ?? false));
  const lineSamples = line ? d3.range(0, 51).map((i) => x.invert(m.l + ((width - m.l - m.r) * i) / 50)) : [];
  return (
    <div ref={ref} className={styles.wrap}>
      <svg width={width} height={height} role="img" aria-label={`${yLabel} against ${xLabel}, ${data.length} points`}>
        <AxisLeft scale={y} x={m.l} grid={width - m.l - m.r} format={yFormat} label={yLabel} />
        <AxisBottom
          scale={x as d3.ScaleLinear<number, number>}
          y={height - m.b}
          format={xFormat ? (v) => xFormat(Number(v)) : undefined}
          label={xLabel}
          tickValues={xLog ? [0.125, 0.25, 0.5, 1, 2, 4, 8].filter((t) => t >= x.domain()[0] && t <= x.domain()[1]) : undefined}
        />
        {zeroLines ? (
          <g stroke="var(--grey-dark)" strokeDasharray="3 3">
            {x.domain()[0] < 0 && x.domain()[1] > 0 ? <line x1={x(0)} x2={x(0)} y1={m.t} y2={height - m.b} /> : null}
            {y.domain()[0] < 0 && y.domain()[1] > 0 ? <line x1={m.l} x2={width - m.r} y1={y(0)} y2={y(0)} /> : null}
          </g>
        ) : null}
        {line ? (
          <path d={d3.line<number>().x((v) => x(v)).y((v) => y(line(v)))(lineSamples) ?? ""} fill="none" stroke="var(--white)" strokeWidth="2" strokeDasharray="8 5" />
        ) : null}
        {sorted.map((d) => {
          const color = d.highlight ? "var(--red)" : d.group && groupColors ? groupColors[d.group] : "var(--grey-dark)";
          return d.highlight ? (
            <rect key={d.key} x={x(d.x) - 5} y={y(d.y) - 5} width="10" height="10" transform={`rotate(45 ${x(d.x)} ${y(d.y)})`} fill={color} stroke="#000" strokeWidth="1.5"
              onMouseEnter={() => setHover(d)} onMouseLeave={() => setHover(null)} />
          ) : (
            <circle key={d.key} cx={x(d.x)} cy={y(d.y)} r="4" fill={color} opacity="0.75" onMouseEnter={() => setHover(d)} onMouseLeave={() => setHover(null)} />
          );
        })}
      </svg>
      {hover ? <span className={styles.tip} style={{ left: x(hover.x), top: y(hover.y) }}>{hover.label}</span> : null}
    </div>
  );
}

function padExt([a, b]: [number, number]): [number, number] {
  const pad = (b - a) * 0.06 || 1;
  return [a - pad, b + pad];
}
