import styles from "./StatBar.module.css";

/** In-game attribute row: label, value, and a segmented bar. `rating` is 0-99
 *  and drives the bar and colour band; `value` is the human-readable figure. */
export function StatBar({ label, value, rating, record = false, sub }: {
  label: string;
  value: string;
  /** null = data missing (shows NO DATA); undefined = no bar for this stat */
  rating?: number | null;
  record?: boolean;
  sub?: string;
}) {
  const r = rating === null || rating === undefined ? null : Math.max(0, Math.min(99, Math.round(rating)));
  const band = r === null ? "none" : r >= 80 ? "high" : r >= 60 ? "mid" : r >= 40 ? "low" : "bad";
  return (
    <div className={styles.row}>
      <span className={styles.label}>{label}{sub ? <em className={styles.sub}>{sub}</em> : null}</span>
      <span className={`${styles.value} ${record ? styles.record : ""}`}>{value}</span>
      {rating === undefined ? null : <span className={styles.track} aria-hidden>
        {r === null ? (
          <span className={styles.nodata}>NO DATA</span>
        ) : (
          <span className={`${styles.fill} ${styles[band]} ${record ? styles.recordFill : ""}`} style={{ width: `${Math.max(3, r)}%` }} />
        )}
      </span>}
    </div>
  );
}
