import type { SigningCard as Card } from "@/lib/data-types";
import { money, num } from "@/lib/format";
import { Badge } from "./Badge";
import styles from "./SigningCard.module.css";

/** Original-design player stat card: initials instead of photos, value bars. */
export function SigningCard({ card, tone }: { card: Card; tone?: "best" | "worst" }) {
  const initials = card.player.split(/\s+/).map((w) => w[0]).join("").slice(0, 3).toUpperCase();
  const minutesBar = Math.min(1, card.league_minutes / 15000);
  return (
    <article className={`${styles.card} ${tone ? styles[tone] : ""}`}>
      <header className={styles.top}>
        <span className={styles.rating}>{card.value_rating}</span>
        <span className={styles.ratingLabel}>VALUE</span>
        <span className={styles.initials}>{initials}</span>
      </header>
      <div className={styles.body}>
        {tone ? <Badge tone={tone === "best" ? "white" : "red"}>{tone === "best" ? "Best value" : "Worst value"}</Badge> : null}
        <h3 className={styles.name}>{card.player}</h3>
        <p className={styles.meta}>{card.position} · {card.season_label} · from {card.from_club}</p>
        <dl className={styles.stats}>
          <div><dt>Fee</dt><dd>{money(card.fee_gbp_real)}</dd></div>
          <div><dt>Resale</dt><dd>{card.still_at_club ? "AT CLUB" : money(card.sale_fee_gbp_real)}</dd></div>
          <div><dt>Lg mins</dt><dd>{card.league_minutes.toLocaleString("en-GB")}</dd></div>
          <div><dt>G+A /90</dt><dd>{num(card.ga_per90)}</dd></div>
        </dl>
        <div className={styles.bar}><span style={{ width: `${minutesBar * 100}%` }} /></div>
        <p className={styles.cost}>
          <strong>{money(card.cost_per_1000_min, 1)}</strong> per 1,000 league minutes
        </p>
      </div>
    </article>
  );
}
