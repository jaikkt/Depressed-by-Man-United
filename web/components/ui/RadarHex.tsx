// Six-axis attribute hexagon. Values are 0-100 percentiles; drawn with plain
// SVG maths so it needs no chart library.

export interface RadarAxis {
  label: string;
  value: number | null; // 0..100
}

export function RadarHex({ axes, size = 220, compare }: { axes: RadarAxis[]; size?: number; compare?: (number | null)[] }) {
  const n = axes.length;
  const c = size / 2;
  const r = size / 2 - 34;
  const point = (i: number, v: number) => {
    const a = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [c + Math.cos(a) * r * (v / 100), c + Math.sin(a) * r * (v / 100)] as const;
  };
  const ring = (v: number) => axes.map((_, i) => point(i, v).join(",")).join(" ");
  const shape = (vals: (number | null)[]) => vals.map((v, i) => point(i, v ?? 0).join(",")).join(" ");
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={axes.map((a) => `${a.label} ${a.value ?? "no data"}`).join(", ")}>
      {[25, 50, 75, 100].map((v) => (
        <polygon key={v} points={ring(v)} fill="none" stroke="var(--panel-line)" strokeWidth={1} />
      ))}
      {axes.map((_, i) => {
        const [x, y] = point(i, 100);
        return <line key={i} x1={c} y1={c} x2={x} y2={y} stroke="var(--panel-line)" />;
      })}
      {compare ? <polygon points={shape(compare)} fill="none" stroke="var(--grey)" strokeDasharray="4 3" strokeWidth={1.5} /> : null}
      <polygon points={shape(axes.map((a) => a.value))} fill="rgba(218,41,28,0.45)" stroke="var(--red)" strokeWidth={2.5} strokeLinejoin="miter" />
      {axes.map((a, i) => {
        const [x, y] = point(i, 122);
        return (
          <text key={a.label} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fill={a.value === null ? "var(--grey-dark)" : "var(--white)"} fontFamily="var(--font-display)" fontWeight={700} fontSize={12} letterSpacing="0.08em">
            {a.label.toUpperCase()}
          </text>
        );
      })}
    </svg>
  );
}
