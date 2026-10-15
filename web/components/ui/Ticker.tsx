import styles from "./Ticker.module.css";

/** Scrolling headline strip. Items are duplicated once so the CSS loop is seamless. */
export function Ticker({ items, label = "LATEST" }: { items: string[]; label?: string }) {
  if (items.length === 0) return null;
  const loop = [...items, ...items];
  return (
    <div className={styles.ticker} role="marquee" aria-label="Headline stats">
      <span className={styles.label}>{label}</span>
      <div className={styles.viewport}>
        <ul className={styles.track} style={{ animationDuration: `${items.length * 9}s` }}>
          {loop.map((t, i) => (
            <li key={i} className={styles.item} aria-hidden={i >= items.length}>
              <span className={styles.dot} />
              {t}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
