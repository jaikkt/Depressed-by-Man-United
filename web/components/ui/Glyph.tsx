"use client";

import { useInputDevice } from "@/lib/input";
import styles from "./Glyph.module.css";

export type Action = "select" | "back" | "info" | "prevTab" | "nextTab" | "move" | "moveH";

const LABELS: Record<Action, { key: string; pad: string; padShape: "round" | "bumper" | "dpad" }> = {
  select: { key: "ENTER", pad: "A", padShape: "round" },
  back: { key: "ESC", pad: "B", padShape: "round" },
  info: { key: "I", pad: "Y", padShape: "round" },
  prevTab: { key: "Q", pad: "LB", padShape: "bumper" },
  nextTab: { key: "E", pad: "RB", padShape: "bumper" },
  move: { key: "↑↓←→", pad: "✣", padShape: "dpad" },
  moveH: { key: "← →", pad: "LB RB", padShape: "bumper" },
};

/** A button glyph that swaps between keyboard keycaps and controller buttons
 *  depending on what the player last touched, like console games do. */
export function Glyph({ action }: { action: Action }) {
  const device = useInputDevice();
  const l = LABELS[action];
  if (device === "gamepad") {
    return <span className={`${styles.pad} ${styles[l.padShape]} ${styles[`pad_${l.pad.replace(/\s/g, "")}`] ?? ""}`}>{l.pad}</span>;
  }
  return <span className={styles.key}>{l.key}</span>;
}
