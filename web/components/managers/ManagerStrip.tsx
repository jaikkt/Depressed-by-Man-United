"use client";

import { useEffect, useRef, type KeyboardEvent } from "react";
import { Badge } from "@/components/ui/Badge";
import { Portrait } from "@/components/ui/Portrait";
import type { Manager } from "@/lib/data-types";
import { year } from "@/lib/format";
import { useSettings } from "@/lib/settings";
import styles from "./ManagerStrip.module.css";

/** Chronological selector strip, like a kit/squad selector. Owns left/right. */
export function ManagerStrip({ managers, index, onSelect }: { managers: Manager[]; index: number; onSelect: (i: number) => void }) {
  const { sfx } = useSettings();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const stripRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Scroll only the strip (scrollIntoView would also scroll the page).
    const strip = stripRef.current;
    const item = refs.current[index];
    if (!strip || !item) return;
    const target = item.offsetLeft - strip.clientWidth / 2 + item.clientWidth / 2;
    strip.scrollTo({ left: target, behavior: "smooth" });
  }, [index]);

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const next = Math.max(0, Math.min(managers.length - 1, index + (e.key === "ArrowRight" ? 1 : -1)));
    if (next !== index) {
      sfx("move");
      onSelect(next);
      refs.current[next]?.focus({ preventScroll: true });
    }
  };

  return (
    <div ref={stripRef} className={styles.strip} data-nav-own="horizontal" onKeyDown={onKey} role="listbox" aria-label="Choose a manager">
      {managers.map((m, i) => (
        <button
          key={m.slug}
          ref={(el) => {
            refs.current[i] = el;
          }}
          type="button"
          role="option"
          aria-selected={i === index}
          className={`${styles.item} ${i === index ? styles.active : ""}`}
          onClick={() => {
            sfx("select");
            onSelect(i);
          }}
          data-nav=""
          data-nav-default={i === index ? "" : undefined}
        >
          <Portrait name={m.name} src={m.portrait} size="sm" />
          <span className={styles.text}>
            <span className={styles.name}>{m.name.split(" ").slice(-1)[0]}</span>
            <span className={styles.years}>{year(m.start)}–{m.end ? year(m.end) : "NOW"}</span>
            {m.interim ? <Badge tone="outline">Interim</Badge> : null}
          </span>
        </button>
      ))}
    </div>
  );
}
