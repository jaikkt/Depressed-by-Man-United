"use client";

import { Glyph, type Action } from "./Glyph";
import styles from "./PromptBar.module.css";

export interface Prompt {
  action: Action;
  label: string;
}

/** Fixed bottom bar listing context actions with live keyboard/controller glyphs. */
export function PromptBar({ prompts, inline = false }: { prompts: Prompt[]; inline?: boolean }) {
  return (
    <nav className={`${styles.bar} ${inline ? styles.inline : ""}`} aria-label="Controls">
      <div className={styles.stripe} />
      <ul className={styles.list}>
        {prompts.map((p) => (
          <li key={p.action + p.label} className={styles.item}>
            <Glyph action={p.action} />
            <span>{p.label}</span>
          </li>
        ))}
      </ul>
      <p className={styles.legal}>Unofficial fan analysis. Not affiliated with Manchester United or EA Sports.</p>
    </nav>
  );
}
