"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { playSound, type UiSound } from "./sound";

interface Settings {
  sounds: boolean;
  reducedMotion: boolean;
}

interface SettingsApi extends Settings {
  setSounds: (on: boolean) => void;
  setReducedMotion: (on: boolean) => void;
  sfx: (kind: UiSound) => void;
}

const STORAGE_KEY = "dbmu-settings";
// Sounds default OFF (spec): never surprise someone with audio.
const DEFAULTS: Settings = { sounds: false, reducedMotion: false };

const SettingsContext = createContext<SettingsApi | null>(null);

function readStored(): Settings {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS;
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return DEFAULTS;
    const p = parsed as Partial<Record<keyof Settings, unknown>>;
    return {
      sounds: typeof p.sounds === "boolean" ? p.sounds : DEFAULTS.sounds,
      reducedMotion: typeof p.reducedMotion === "boolean" ? p.reducedMotion : DEFAULTS.reducedMotion,
    };
  } catch {
    return DEFAULTS;
  }
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(DEFAULTS);

  useEffect(() => {
    const stored = readStored();
    const osReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // Hydrate from storage after mount: localStorage is not available during static rendering.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSettings({ ...stored, reducedMotion: stored.reducedMotion || osReduced });
  }, []);

  useEffect(() => {
    document.documentElement.dataset.reducedMotion = String(settings.reducedMotion);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
      /* private mode: settings just won't persist */
    }
  }, [settings]);

  const setSounds = useCallback((on: boolean) => setSettings((s) => ({ ...s, sounds: on })), []);
  const setReducedMotion = useCallback((on: boolean) => setSettings((s) => ({ ...s, reducedMotion: on })), []);
  const sfx = useCallback(
    (kind: UiSound) => {
      if (settings.sounds) playSound(kind);
    },
    [settings.sounds],
  );

  const api = useMemo<SettingsApi>(
    () => ({ ...settings, setSounds, setReducedMotion, sfx }),
    [settings, setSounds, setReducedMotion, sfx],
  );
  return <SettingsContext.Provider value={api}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsApi {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used inside SettingsProvider");
  return ctx;
}
