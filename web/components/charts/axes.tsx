import type { ScaleLinear, ScaleTime } from "d3";

// Custom axes drawn in React (not d3-axis) so type, colour and tick style match
// the game UI exactly: condensed uppercase labels, no domain line clutter.

type AnyScale = ScaleLinear<number, number> | ScaleTime<number, number>;

export function AxisBottom({ scale, y, ticks = 6, format, label, tickValues }: {
  scale: AnyScale;
  y: number;
  ticks?: number;
  format?: (v: number | Date) => string;
  label?: string;
  tickValues?: number[]; // explicit ticks, e.g. for log scales whose default ticks crowd
}) {
  const values = tickValues ?? (scale.ticks as (n: number) => (number | Date)[])(ticks);
  const [x0, x1] = scale.range();
  return (
    <g transform={`translate(0 ${y})`}>
      <line x1={x0} x2={x1} stroke="var(--grey-dark)" />
      {values.map((v, i) => {
        const x = (scale as (v: number | Date) => number)(v);
        return (
          <g key={i} transform={`translate(${x} 0)`}>
            <line y2="6" stroke="var(--grey-dark)" />
            <text y="20" textAnchor="middle" fill="var(--grey)" fontFamily="var(--font-display)" fontSize="12" fontWeight="600">
              {format ? format(v) : String(v)}
            </text>
          </g>
        );
      })}
      {label ? (
        <text x={x1} y="38" textAnchor="end" fill="var(--grey)" fontFamily="var(--font-display)" fontSize="12" fontWeight="700" letterSpacing="0.12em">
          {label.toUpperCase()}
        </text>
      ) : null}
    </g>
  );
}

export function AxisLeft({ scale, x, ticks = 5, format, label, grid = 0 }: {
  scale: ScaleLinear<number, number>;
  x: number;
  ticks?: number;
  format?: (v: number) => string;
  label?: string;
  grid?: number; // width of horizontal grid lines, 0 = none
}) {
  const values = scale.ticks(ticks);
  return (
    <g transform={`translate(${x} 0)`}>
      {values.map((v) => (
        <g key={v} transform={`translate(0 ${scale(v)})`}>
          {grid > 0 ? <line x2={grid} stroke="var(--panel-line)" strokeDasharray="2 4" /> : null}
          <text x="-8" dy="4" textAnchor="end" fill="var(--grey)" fontFamily="var(--font-display)" fontSize="12" fontWeight="600">
            {format ? format(v) : String(v)}
          </text>
        </g>
      ))}
      {label ? (
        <text x="0" y={scale.range()[1] - 12} textAnchor="start" fill="var(--grey)" fontFamily="var(--font-display)" fontSize="12" fontWeight="700" letterSpacing="0.12em">
          {label.toUpperCase()}
        </text>
      ) : null}
    </g>
  );
}
