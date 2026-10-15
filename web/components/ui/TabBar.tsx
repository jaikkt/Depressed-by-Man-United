"use client";

import { motion } from "framer-motion";
import { useKey } from "@/lib/input";
import { useSettings } from "@/lib/settings";
import { Glyph } from "./Glyph";
import styles from "./TabBar.module.css";

export interface Tab<T extends string> {
  id: T;
  label: string;
}

/** Top tabs switched with Q/E (keyboard) or LB/RB (controller). The red
 *  underline slides between tabs via a shared layout animation. */
export function TabBar<T extends string>({ tabs, value, onChange, layoutId = "tab-underline" }: {
  tabs: Tab<T>[];
  value: T;
  onChange: (id: T) => void;
  layoutId?: string;
}) {
  const { sfx } = useSettings();
  const index = tabs.findIndex((t) => t.id === value);
  const go = (delta: number) => {
    const next = tabs[(index + delta + tabs.length) % tabs.length];
    sfx("move");
    onChange(next.id);
  };
  useKey(["q"], () => go(-1));
  useKey(["e"], () => go(1));

  return (
    <div className={styles.bar} role="tablist">
      <span className={styles.glyph}><Glyph action="prevTab" /></span>
      {tabs.map((t) => (
        <button
          key={t.id}
          type="button"
          role="tab"
          aria-selected={t.id === value}
          className={`${styles.tab} ${t.id === value ? styles.active : ""}`}
          onClick={() => {
            sfx("select");
            onChange(t.id);
          }}
          data-nav=""
        >
          <span>{t.label}</span>
          {t.id === value ? <motion.span layoutId={layoutId} className={styles.underline} transition={{ duration: 0.2, ease: [0.2, 0.9, 0.2, 1] }} /> : null}
        </button>
      ))}
      <span className={styles.glyph}><Glyph action="nextTab" /></span>
    </div>
  );
}
