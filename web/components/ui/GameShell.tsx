"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { Button } from "./Button";
import { Logo } from "./Logo";
import { PromptBar, type Prompt } from "./PromptBar";
import styles from "./GameShell.module.css";

/** Frame used by every mode screen: header strip, animated content, prompt bar. */
export function GameShell({ title, kicker, children, prompts, headerRight }: {
  title: string;
  kicker?: string;
  children: ReactNode;
  prompts?: Prompt[];
  headerRight?: ReactNode;
}) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Logo size={40} />
        <div className={styles.titles}>
          {kicker ? <span className={styles.kicker}>{kicker}</span> : null}
          <h1 className={styles.title}>{title}</h1>
        </div>
        <div className={styles.right}>
          {headerRight}
          <Button href="/" variant="secondary" glyph="back">Main Menu</Button>
        </div>
      </header>
      <div className="kit-stripes" />
      <motion.main
        className={styles.main}
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.22, ease: [0.2, 0.9, 0.2, 1] }}
      >
        {children}
      </motion.main>
      <PromptBar prompts={prompts ?? [{ action: "move", label: "Navigate" }, { action: "select", label: "Select" }, { action: "back", label: "Back" }]} />
    </div>
  );
}
