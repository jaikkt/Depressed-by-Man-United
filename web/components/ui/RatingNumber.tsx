import styles from "./RatingNumber.module.css";

/** Big boxed rating number, the "OVR" block from a player card, in original styling. */
export function RatingNumber({ value, label, tone = "auto", size = "md" }: {
  value: number | null;
  label: string;
  tone?: "auto" | "gold" | "red" | "white";
  size?: "md" | "lg";
}) {
  const resolved = tone !== "auto" ? tone : value === null ? "white" : value >= 80 ? "white" : value >= 50 ? "red" : "red";
  return (
    <div className={`${styles.box} ${styles[resolved]} ${styles[size]}`}>
      <span className={styles.value}>{value === null ? "--" : Math.round(value)}</span>
      <span className={styles.label}>{label}</span>
    </div>
  );
}
