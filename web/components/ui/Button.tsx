"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useSettings } from "@/lib/settings";
import { Glyph, type Action } from "./Glyph";
import styles from "./Button.module.css";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps {
  children: ReactNode;
  glyph?: Action;
  variant?: Variant;
  size?: "md" | "lg";
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  /** Only for the /kit page: render a state statically so every state is visible at once. */
  forceState?: "hover" | "pressed";
  navDefault?: boolean;
  ariaLabel?: string;
  active?: boolean;
}

export function Button({ children, glyph, variant = "primary", size = "md", href, onClick, disabled, forceState, navDefault, ariaLabel, active }: ButtonProps) {
  const { sfx } = useSettings();
  const className = [
    styles.button,
    styles[variant],
    styles[size],
    forceState ? styles[`force_${forceState}`] : "",
    active ? styles.active : "",
  ].join(" ");
  const inner = (
    <span className={styles.face}>
      {glyph ? <Glyph action={glyph} /> : null}
      <span className={styles.label}>{children}</span>
    </span>
  );
  const common = {
    className,
    "data-nav": "",
    "data-nav-default": navDefault ? "" : undefined,
    onFocus: () => sfx("move"),
    "aria-label": ariaLabel,
  };
  if (href && !disabled) {
    return (
      <Link href={href} {...common} onClick={() => sfx("select")}>
        {inner}
      </Link>
    );
  }
  return (
    <button
      type="button"
      {...common}
      disabled={disabled}
      aria-pressed={active}
      onClick={() => {
        sfx("select");
        onClick?.();
      }}
    >
      {inner}
    </button>
  );
}
