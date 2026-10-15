"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";

export type InputDevice = "keyboard" | "gamepad";

const InputContext = createContext<InputDevice>("keyboard");

// Standard Gamepad mapping (W3C "standard" layout, used by Xbox/PS pads in browsers).
const BUTTON_TO_KEY: Record<number, string> = {
  0: "Enter", // A / Cross
  1: "Escape", // B / Circle
  3: "i", // Y / Triangle
  4: "q", // LB
  5: "e", // RB
  12: "ArrowUp",
  13: "ArrowDown",
  14: "ArrowLeft",
  15: "ArrowRight",
};
const AXIS_THRESHOLD = 0.6;
const REPEAT_MS = 180;

function emitKey(key: string): void {
  // Synthetic key events can't "press" a button, so A clicks the focused element
  // directly; everything else is dispatched as a keydown that our handlers read.
  if (key === "Enter") {
    const el = document.activeElement;
    if (el instanceof HTMLElement && el !== document.body) {
      el.click();
      return;
    }
  }
  window.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
}

/** Tracks the last input device (for prompt glyphs) and turns gamepad input
 *  into the same key events the keyboard produces, so every screen only has to
 *  handle keys. */
export function InputProvider({ children }: { children: ReactNode }) {
  const [device, setDevice] = useState<InputDevice>("keyboard");
  const lastPress = useRef<Record<string, number>>({});

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.isTrusted) setDevice("keyboard");
    };
    window.addEventListener("keydown", onKey);

    let frame = 0;
    const poll = () => {
      const pads = typeof navigator.getGamepads === "function" ? navigator.getGamepads() : [];
      const now = performance.now();
      for (const pad of pads) {
        if (!pad) continue;
        const pressed: string[] = [];
        pad.buttons.forEach((b, i) => {
          const key = BUTTON_TO_KEY[i];
          if (key && b.pressed) pressed.push(key);
        });
        const [x = 0, y = 0] = pad.axes;
        if (x < -AXIS_THRESHOLD) pressed.push("ArrowLeft");
        if (x > AXIS_THRESHOLD) pressed.push("ArrowRight");
        if (y < -AXIS_THRESHOLD) pressed.push("ArrowUp");
        if (y > AXIS_THRESHOLD) pressed.push("ArrowDown");
        for (const key of pressed) {
          const last = lastPress.current[key] ?? 0;
          if (now - last > REPEAT_MS) {
            lastPress.current[key] = now;
            setDevice("gamepad");
            emitKey(key);
          }
        }
        // Releasing a button allows an immediate re-press.
        for (const key of Object.keys(lastPress.current)) {
          if (!pressed.includes(key)) delete lastPress.current[key];
        }
      }
      frame = requestAnimationFrame(poll);
    };
    frame = requestAnimationFrame(poll);
    return () => {
      window.removeEventListener("keydown", onKey);
      cancelAnimationFrame(frame);
    };
  }, []);

  return <InputContext.Provider value={device}>{children}</InputContext.Provider>;
}

export function useInputDevice(): InputDevice {
  return useContext(InputContext);
}

/** Subscribe to a key while a component is mounted. Handlers run before the
 *  global navigation handler (children's effects register first), so calling
 *  e.preventDefault() stops the global behaviour (e.g. Esc = back). */
export function useKey(keys: string[], handler: (e: KeyboardEvent) => void, enabled = true): void {
  const ref = useRef(handler);
  useEffect(() => {
    ref.current = handler;
  });
  const keyList = keys.join("|");
  useEffect(() => {
    if (!enabled) return;
    const wanted = new Set(keyList.split("|").map((k) => k.toLowerCase()));
    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented) return;
      if (isTyping(e)) return;
      if (wanted.has(e.key.toLowerCase())) ref.current(e);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [keyList, enabled]);
}

export function isTyping(e: KeyboardEvent): boolean {
  const t = e.target;
  return t instanceof HTMLInputElement || t instanceof HTMLTextAreaElement || t instanceof HTMLSelectElement;
}
