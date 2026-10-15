import type { XIPlayer } from "@/lib/data-types";
import styles from "./Pitch.module.css";

// Vertical pitch with the most common XI as markers. Coordinates come straight
// from Transfermarkt's line-up template (top: 0 = attacking end, ~80 = own goal;
// left: 0-75 = box left edge), so we only rescale them into the SVG.
const W = 340;
const H = 460;

function place(p: XIPlayer): [number, number] {
  const x = ((p.left + 5) / 85) * (W - 60) + 30;
  const y = (p.top / 82) * (H - 90) + 45;
  return [x, y];
}

function surname(name: string): string {
  const parts = name.split(" ");
  return (parts.length > 1 ? parts.slice(1).join(" ") : name).toUpperCase();
}

export function Pitch({ xi, maxStarts }: { xi: XIPlayer[]; maxStarts: number }) {
  return (
    <svg className={styles.pitch} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Most common XI: ${xi.map((p) => `${p.pos} ${p.name} (${p.starts} starts)`).join(", ")}`}>
      <defs>
        <pattern id="mow" width={W} height="46" patternUnits="userSpaceOnUse">
          <rect width={W} height="23" fill="#151517" />
          <rect y="23" width={W} height="23" fill="#19191c" />
        </pattern>
      </defs>
      <rect x="0" y="0" width={W} height={H} fill="url(#mow)" />
      <g fill="none" stroke="rgba(244,241,234,0.25)" strokeWidth="2">
        <rect x="12" y="12" width={W - 24} height={H - 24} />
        <line x1="12" y1={H / 2} x2={W - 12} y2={H / 2} />
        <circle cx={W / 2} cy={H / 2} r="44" />
        <rect x={W / 2 - 80} y="12" width="160" height="70" />
        <rect x={W / 2 - 36} y="12" width="72" height="26" />
        <rect x={W / 2 - 80} y={H - 82} width="160" height="70" />
        <rect x={W / 2 - 36} y={H - 38} width="72" height="26" />
      </g>
      {xi.map((p) => {
        const [x, y] = place(p);
        const strength = maxStarts > 0 ? p.starts / maxStarts : 0;
        return (
          <g key={p.player_id} transform={`translate(${x} ${y})`} className={styles.marker}>
            <polygon points="-15,-13 15,-13 12,13 -12,13" fill={p.pos === "GK" ? "var(--white)" : "var(--red)"} stroke="#000" strokeWidth="2" />
            <text y="5" textAnchor="middle" className={styles.pos} fill={p.pos === "GK" ? "var(--black)" : "var(--white)"}>{p.pos}</text>
            <rect x="-42" y="17" width="84" height="16" fill="#000" opacity="0.85" />
            <text y="29" textAnchor="middle" className={styles.name}>{surname(p.name).slice(0, 13)}</text>
            <rect x="-42" y="34" width={84 * strength} height="3" fill="var(--white)" />
            <text y="49" textAnchor="middle" className={styles.starts}>{p.starts} STARTS</text>
          </g>
        );
      })}
    </svg>
  );
}
