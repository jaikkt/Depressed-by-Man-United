"use client";

import { motion } from "framer-motion";
import { Icon } from "./Icon";
import styles from "./LoadingScreen.module.css";

/** Between-modes loading card with a "DID YOU KNOW?" tip and a spinning ball. */
export function LoadingScreen({ tip, mode }: { tip?: string; mode?: string }) {
  return (
    <motion.div className={styles.screen} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }} role="status" aria-live="polite">
      <div className={styles.inner}>
        {mode ? <p className={styles.mode}>LOADING {mode}</p> : null}
        <div className={styles.tip}>
          <span className={styles.tipLabel}>DID YOU KNOW?</span>
          <p>{tip ?? "Every number on this site is recomputed from raw results, not copied from a headline."}</p>
        </div>
      </div>
      <span className={styles.ball}><Icon name="ball" size={40} /></span>
    </motion.div>
  );
}
