"use client";

import * as d3 from "d3";
import { useState, type MouseEvent } from "react";
import { AxisBottom, AxisLeft } from "./axes";
import styles from "./ChartTooltip.module.css";
import { useWidth } from "./useWidth";

export interface LineSeries {
  id: string;
  label: string;
  color: string;
  width?: number;
  dash?: string;
  points: { x: number | Date; y: number }[];
}

export interface Marker {
  x: number | Date;
  label: string;
  strength: number; // 0..1, drives opacity
}

export interface SegmentLine {
  x0: number | Date;
  x1: number | Date;
  y: number;
}

/** Multi-series line chart with optional vertical markers (change points),
 *  segment means and a horizontal reference line. X can be dates or numbers. */
export function LineChart({ series, height = 340, yLabel, xLabel, markers = [], segments = [], reference, yFormat, xFormat, yDomain, legend = true }: {
  series: LineSeries[];
  height?: number;
  yLabel: string;
  xLabel?: string;
  markers?: Marker[];
  segments?: SegmentLine[];
  reference?: { y: number; label: string };
  yFormat?: (v: number) => string;
  xFormat?: (v: number | Date) => string;
  yDomain?: [number, number];
  legend?: boolean;
}) {
  const { ref, width } = useWidth<HTMLDivElement>();
  const [hoverX, setHoverX] = useState<number | null>(null);
  const m = { t: 22, r: 18, b: 44, l: 54 };
  const all = series.flatMap((s) => s.points);
  const isDate = all.length > 0 && all[0].x instanceof Date;
  const xExt = d3.extent(all, (p) => +p.x) as [number, number];
  const x = isDate
    ? d3.scaleTime().domain([new Date(xExt[0]), new Date(xExt[1])]).range([m.l, width - m.r])
    : d3.scaleLinear().domain(xExt).range([m.l, width - m.r]);
  const yExt = yDomain ?? (d3.extent([...all.map((p) => p.y), ...(reference ? [reference.y] : [])]) as [number, number]);
  const y = d3.scaleLinear().domain(yExt).range([height - m.b, m.t]).nice();
  const sx = (v: number | Date) => (x as (v: number | Date) => number)(v);
  const line = d3.line<{ x: number | Date; y: number }>().x((p) => sx(p.x)).y((p) => y(p.y)).curve(d3.curveMonotoneX);

  const onMove = (e: MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setHoverX(e.clientX - rect.left);
  };
  const hoverValues = hoverX === null ? [] : series.map((s) => {
    const target = (x as d3.ScaleLinear<number, number>).invert(hoverX);
    const i = d3.bisector((p: { x: number | Date }) => +p.x).center(s.points, +target);
    return { s, p: s.points[i] };
  }).filter((v) => v.p);

  return (
    <div ref={ref} className={styles.wrap}>
      <svg width={width} height={height} onMouseMove={onMove} onMouseLeave={() => setHoverX(null)} role="img" aria-label={`${yLabel}: ${series.map((s) => s.label).join(", ")}`}>
        <AxisLeft scale={y} x={m.l} grid={width - m.l - m.r} format={yFormat} label={yLabel} />
        <AxisBottom scale={x} y={height - m.b} format={xFormat} label={xLabel} />
        {reference ? (
          <g>
            <line x1={m.l} x2={width - m.r} y1={y(reference.y)} y2={y(reference.y)} stroke="var(--white)" strokeDasharray="6 4" opacity="0.6" />
            <text x={width - m.r} y={y(reference.y) - 6} textAnchor="end" fill="var(--grey)" fontFamily="var(--font-display)" fontSize="12" fontWeight="700" letterSpacing="0.1em">{reference.label}</text>
          </g>
        ) : null}
        {markers.map((mk, i) => (
          <g key={i} opacity={0.25 + 0.75 * mk.strength}>
            <line x1={sx(mk.x)} x2={sx(mk.x)} y1={m.t} y2={height - m.b} stroke="var(--gold)" strokeWidth={mk.strength >= 0.99 ? 3 : 1.5} strokeDasharray={mk.strength >= 0.5 ? undefined : "3 3"} />
            {mk.strength >= 0.5 ? (
              <text x={sx(mk.x) + 4} y={m.t + 10 + (i % 3) * 14} fill="var(--gold)" fontFamily="var(--font-display)" fontSize="12" fontWeight="800">{mk.label}</text>
            ) : null}
          </g>
        ))}
        {segments.map((sg, i) => (
          <line key={i} x1={sx(sg.x0)} x2={sx(sg.x1)} y1={y(sg.y)} y2={y(sg.y)} stroke="var(--white)" strokeWidth="4" opacity="0.85" />
        ))}
        {series.map((s) => (
          <path key={s.id} d={line(s.points) ?? ""} fill="none" stroke={s.color} strokeWidth={s.width ?? 2} strokeDasharray={s.dash} />
        ))}
        {hoverX !== null && hoverValues.length ? (
          <line x1={hoverX} x2={hoverX} y1={m.t} y2={height - m.b} stroke="var(--grey)" strokeWidth="1" />
        ) : null}
      </svg>
      {hoverX !== null && hoverValues.length ? (
        <span className={styles.tip} style={{ left: hoverX, top: m.t + 8, transform: "translate(8px, 0)" }}>
          {xFormat ? xFormat(hoverValues[0].p.x) : String(hoverValues[0].p.x)} ·{" "}
          {hoverValues.slice(0, 3).map((v) => `${v.s.label} ${yFormat ? yFormat(v.p.y) : v.p.y.toFixed(2)}`).join(" · ")}
        </span>
      ) : null}
      {legend && series.length > 1 ? (
        <div className={styles.legend}>
          {series.map((s) => (
            <span key={s.id} className={styles.legendItem}><span className={styles.swatch} style={{ background: s.color }} />{s.label}</span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
