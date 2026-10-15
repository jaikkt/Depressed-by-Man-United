"use client";

import { motion } from "framer-motion";
import { useEffect } from "react";
import { Glyph } from "@/components/ui/Glyph";
import { Logo } from "@/components/ui/Logo";
import { useSettings } from "@/lib/settings";
import styles from "./TitleScreen.module.css";

/** "PRESS ENTER" attract screen shown on first load of a session. */
export function TitleScreen({ onStart }: { onStart: () => void }) {
  const { sfx } = useSettings();
  useEffect(() => {
    const go = (e: KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        sfx("select");
        onStart();
      }
    };
    window.addEventListener("keydown", go);
    return () => window.removeEventListener("keydown", go);
  }, [onStart, sfx]);

  return (
    <motion.div
      className={`${styles.screen} scanlines`}
      exit={{ opacity: 0, scale: 1.04 }}
      transition={{ duration: 0.22, ease: [0.2, 0.9, 0.2, 1] }}
      onClick={() => {
        sfx("select");
        onStart();
      }}
      role="button"
      tabIndex={0}
      aria-label="Press Enter to start"
    >
      <div className={styles.stripes} aria-hidden />
      <motion.div className={styles.block} initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.25, delay: 0.05 }}>
        <Logo size={110} />
        <h1 className={styles.title}>
          <span className={styles.l1}>Depressed</span>
          <span className={styles.l2}>by</span>
          <span className={styles.l3}>ManUTD</span>
        </h1>
        <p className={styles.sub}>What the money should have bought, 1992 to now</p>
      </motion.div>
      <p className={styles.press}>
        PRESS <Glyph action="select" /> TO START
      </p>
      <p className={styles.legal}>Unofficial fan analysis. Not affiliated with Manchester United or EA Sports.</p>
    </motion.div>
  );
}
