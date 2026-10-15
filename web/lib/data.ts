"use client";

import { useEffect, useState } from "react";
import type { DataFiles } from "./data-types";

// Data is fetched client-side from /data/*.json (written by analysis/export.py).
// A module-level cache means moving between screens never refetches.
const cache = new Map<string, unknown>();

export interface DataState<T> {
  data: T | null;
  error: string | null;
}

export function useData<K extends keyof DataFiles>(file: K): DataState<DataFiles[K]> {
  const [state, setState] = useState<DataState<DataFiles[K]>>(() => ({
    data: (cache.get(file) as DataFiles[K] | undefined) ?? null,
    error: null,
  }));

  useEffect(() => {
    if (cache.has(file)) return;
    let alive = true;
    fetch(`/data/${file}`)
      .then((r) => {
        if (!r.ok) throw new Error(`${file}: HTTP ${r.status}`);
        return r.json() as Promise<DataFiles[K]>;
      })
      .then((json) => {
        cache.set(file, json);
        if (alive) setState({ data: json, error: null });
      })
      .catch((e: unknown) => {
        if (alive) setState({ data: null, error: e instanceof Error ? e.message : String(e) });
      });
    return () => {
      alive = false;
    };
  }, [file]);

  return state;
}
