/* eslint-disable @next/next/no-img-element -- static export, images are pre-sized local files */
import styles from "./Portrait.module.css";

export interface PortraitCredit {
  title: string;
  author: string;
  license: string;
  source_url: string;
}

/** Manager portrait with the game treatment (duotone, halftone, angled crop).
 *  Falls back to stylised initials when no freely licensed photo exists. */
export function Portrait({ name, src, credit, size = "lg" }: { name: string; src: string | null; credit?: PortraitCredit | null; size?: "lg" | "sm" }) {
  const initials = name
    .split(/\s+/)
    .filter((w) => /^[A-ZÀ-Ý]/.test(w))
    .map((w) => w[0])
    .slice(0, 3)
    .join("");
  return (
    <figure className={`${styles.figure} ${styles[size]}`}>
      <div className={styles.frame}>
        {src ? (
          <img className={styles.photo} src={src} alt={`Portrait of ${name}`} />
        ) : (
          <div className={styles.fallback} aria-label={`${name} (no free-licence photo available)`}>
            <span>{initials}</span>
          </div>
        )}
        <div className={`${styles.tone} halftone`} aria-hidden />
      </div>
      {size === "lg" ? (
        <figcaption className={styles.credit}>
          {credit ? (
            <>
              Photo: <a href={credit.source_url} target="_blank" rel="noreferrer">{credit.author}</a>, {credit.license}
            </>
          ) : (
            "No freely licensed photo found"
          )}
        </figcaption>
      ) : null}
    </figure>
  );
}
