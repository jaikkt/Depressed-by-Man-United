import styles from "./Gauge.module.css";

/** Half-dial probability gauge, like a stamina meter. */
export function Gauge({ value, label, tone = "red" }: { value: number | null; label: string; tone?: "red" | "gold" | "white" }) {
  const v = value === null ? 0 : Math.max(0, Math.min(1, value));
  const r = 70;
  const c = Math.PI * r;
  const color = tone === "gold" ? "var(--gold)" : tone === "white" ? "var(--white)" : "var(--red)";
  return (
    <figure className={styles.gauge}>
      <svg viewBox="0 0 180 104" role="img" aria-label={`${label}: ${value === null ? "no data" : `${(v * 100).toFixed(1)}%`}`}>
        <path d="M20 94 A70 70 0 0 1 160 94" fill="none" stroke="#26262b" strokeWidth="18" strokeDasharray="6 3" />
        <path d="M20 94 A70 70 0 0 1 160 94" fill="none" stroke={color} strokeWidth="18" strokeDasharray={`${v * c} ${c}`} style={{ transition: "stroke-dasharray 400ms var(--ease-snap)" }} />
        <text x="90" y="88" textAnchor="middle" className={styles.value}>{value === null ? "--" : value < 0.001 && value > 0 ? "<0.1%" : `${(v * 100).toFixed(v < 0.1 ? 1 : 0)}%`}</text>
      </svg>
      <figcaption className={styles.label}>{label}</figcaption>
    </figure>
  );
}
