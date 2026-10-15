"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useSettings } from "@/lib/settings";
import styles from "./Tile.module.css";

interface TileProps {
  href: string;
  label: string;
  kicker?: string;
  children?: ReactNode; // the graphic area
  size?: "hero" | "wide" | "tall" | "small";
  navDefault?: boolean;
  locked?: boolean;
  forceState?: "hover";
  className?: string;
}

/** Hub tile: graphic area + label bar, slanted cut corner, same focus language as Button. */
export function Tile({ href, label, kicker, children, size = "small", navDefault, locked, forceState, className }: TileProps) {
  const { sfx } = useSettings();
  return (
    <Link
      href={href}
      className={`${styles.tile} ${styles[size]} ${forceState ? styles.force_hover : ""} ${locked ? styles.locked : ""} ${className ?? ""}`}
      data-nav=""
      data-nav-default={navDefault ? "" : undefined}
      onFocus={() => sfx("move")}
      onClick={() => sfx("select")}
    >
      <span className={styles.art}>{children}</span>
      <span className={styles.bar}>
        {kicker ? <span className={styles.kicker}>{kicker}</span> : null}
        <span className={styles.label}>{label}</span>
      </span>
    </Link>
  );
}
