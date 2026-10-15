import styles from "./Logo.module.css";

// Original "DBMU" monogram. The shield top has two notches cut like horns, a
// nod to the "Red Devils" nickname without borrowing anything from the crest.
export function Logo({ size = 56, withWordmark = false }: { size?: number; withWordmark?: boolean }) {
  return (
    <span className={styles.wrap}>
      <svg width={size} height={size * 1.1} viewBox="0 0 100 110" aria-label="DBMU monogram" role="img">
        <path
          d="M8 18 L22 4 L30 18 L70 18 L78 4 L92 18 L92 66 Q92 92 50 106 Q8 92 8 66 Z"
          fill="var(--red)"
          stroke="var(--black)"
          strokeWidth="4"
        />
        <path d="M14 24 L86 24 L86 64 Q86 86 50 99 Q14 86 14 64 Z" fill="none" stroke="var(--white)" strokeWidth="2" />
        <text x="50" y="57" textAnchor="middle" fontFamily="var(--font-display)" fontWeight="800" fontSize="30" fill="var(--white)" letterSpacing="-1">
          DB
        </text>
        <text x="50" y="84" textAnchor="middle" fontFamily="var(--font-display)" fontWeight="800" fontSize="30" fill="var(--black)" letterSpacing="-1">
          MU
        </text>
      </svg>
      {withWordmark ? (
        <span className={styles.word}>
          <span>Depressed</span>
          <span className={styles.by}>by</span>
          <span className={styles.red}>ManUTD</span>
        </span>
      ) : null}
    </span>
  );
}
