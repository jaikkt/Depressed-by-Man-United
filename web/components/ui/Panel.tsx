import type { ReactNode } from "react";
import styles from "./Panel.module.css";

/** Dark angled panel with a red header strip and a thin top highlight. */
export function Panel({ title, kicker, children, className, right, tone = "default" }: {
  title?: string;
  kicker?: string;
  children: ReactNode;
  className?: string;
  right?: ReactNode;
  tone?: "default" | "raised";
}) {
  return (
    <section className={`${styles.panel} ${tone === "raised" ? styles.raised : ""} ${className ?? ""}`}>
      {title ? (
        <header className={styles.header}>
          <h2 className={styles.title}>
            {kicker ? <span className={styles.kicker}>{kicker}</span> : null}
            {title}
          </h2>
          {right ? <div className={styles.right}>{right}</div> : null}
        </header>
      ) : null}
      <div className={styles.body}>{children}</div>
    </section>
  );
}
