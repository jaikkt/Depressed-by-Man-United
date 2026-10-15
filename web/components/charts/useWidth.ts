"use client";

import { useEffect, useRef, useState } from "react";

/** Measure a container so SVG charts can draw at real pixel width (crisp type,
 *  no stretched strokes) instead of scaling a fixed viewBox. */
export function useWidth<T extends HTMLElement>(fallback = 640) {
  const ref = useRef<T | null>(null);
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.max(280, Math.floor(entry.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return { ref, width };
}
