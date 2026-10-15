import type { ReactNode } from "react";
import styles from "./Badge.module.css";

export function Badge({ children, tone = "red" }: { children: ReactNode; tone?: "red" | "white" | "gold" | "outline" }) {
  return <span className={`${styles.badge} ${styles[tone]}`}>{children}</span>;
}
