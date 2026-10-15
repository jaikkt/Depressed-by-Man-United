import styles from "./NoData.module.css";

/** The game-styled empty state. We never invent numbers: missing data looks like this. */
export function NoData({ label = "NO DATA", detail, compact = false }: { label?: string; detail?: string; compact?: boolean }) {
  return (
    <div className={`${styles.box} ${compact ? styles.compact : ""}`}>
      <span className={styles.label}>{label}</span>
      {detail ? <span className={styles.detail}>{detail}</span> : null}
    </div>
  );
}
