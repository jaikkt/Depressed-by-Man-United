"use client";

import * as d3 from "d3";
import type { TimelinePoint } from "@/lib/data-types";
import { AxisLeft } from "./axes";

/** Mini tenure timeline: per-game points as ticks, 10-game rolling PPG as a line,
 *  with the club's PL-era average as a reference. */
export function PpgTimeline({ points, reference, width = 640, height = 170 }: {
  points: TimelinePoint[];
  reference: number;
  width?: number;
  height?: number;
}) {
  const m = { t: 14, r: 12, b: 22, l: 36 };
  const x = d3.scaleLinear().domain([0, Math.max(1, points.length - 1)]).range([m.l, width - m.r]);
  const y = d3.scaleLinear().domain([0, 3]).range([height - m.b, m.t]);
  const line = d3.line<TimelinePoint>().x((p) => x(p.i)).y((p) => y(p.rolling)).curve(d3.curveMonotoneX);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label={`Rolling 10-game points per game over ${points.length} league games`}>
      <AxisLeft scale={y} x={m.l} ticks={3} grid={width - m.l - m.r} format={(v) => v.toFixed(1)} label="PPG" />
      <line x1={m.l} x2={width - m.r} y1={y(reference)} y2={y(reference)} stroke="var(--white)" strokeDasharray="6 4" opacity="0.5" />
      <text x={width - m.r} y={y(reference) - 6} textAnchor="end" fill="var(--grey)" fontSize="11" fontFamily="var(--font-display)" fontWeight="700" letterSpacing="0.1em">
        PL-ERA AVG {reference.toFixed(2)}
      </text>
      {points.map((p) => (
        <rect key={p.i} x={x(p.i) - 1} y={height - m.b + 4} width="2" height="6" fill={p.pts === 3 ? "var(--white)" : p.pts === 1 ? "var(--grey)" : "var(--red)"} />
      ))}
      <path d={line(points) ?? ""} fill="none" stroke="var(--red)" strokeWidth="3" />
    </svg>
  );
}
