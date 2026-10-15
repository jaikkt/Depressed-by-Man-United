// Console-style spatial navigation: arrow keys move focus to the nearest
// focusable [data-nav] element in that direction, judged by on-screen geometry
// rather than DOM order. That's what makes a tile hub feel like a game menu.

export type Direction = "up" | "down" | "left" | "right";

const ARROWS: Record<string, Direction> = {
  ArrowUp: "up",
  ArrowDown: "down",
  ArrowLeft: "left",
  ArrowRight: "right",
};

export function directionFromKey(key: string): Direction | null {
  return ARROWS[key] ?? null;
}

interface Box {
  el: HTMLElement;
  cx: number;
  cy: number;
  rect: DOMRect;
}

function boxes(): Box[] {
  const els = Array.from(document.querySelectorAll<HTMLElement>("[data-nav]"));
  return els
    .filter((el) => !el.hasAttribute("disabled") && el.offsetParent !== null)
    .map((el) => {
      const rect = el.getBoundingClientRect();
      return { el, rect, cx: rect.left + rect.width / 2, cy: rect.top + rect.height / 2 };
    });
}

/** Score candidates: distance along the travel axis plus a heavier penalty for
 *  drifting sideways, so "down" prefers the tile directly below over a closer
 *  one that is far off to the side. */
export function pickNext(from: DOMRect, dir: Direction, candidates: Box[]): HTMLElement | null {
  const fx = from.left + from.width / 2;
  const fy = from.top + from.height / 2;
  let best: HTMLElement | null = null;
  let bestScore = Infinity;
  for (const c of candidates) {
    const dx = c.cx - fx;
    const dy = c.cy - fy;
    let primary: number;
    let ortho: number;
    if (dir === "left") { primary = -dx; ortho = Math.abs(dy); }
    else if (dir === "right") { primary = dx; ortho = Math.abs(dy); }
    else if (dir === "up") { primary = -dy; ortho = Math.abs(dx); }
    else { primary = dy; ortho = Math.abs(dx); }
    if (primary <= 4) continue;
    const score = primary + ortho * 2.2;
    if (score < bestScore) {
      bestScore = score;
      best = c.el;
    }
  }
  return best;
}

export function moveFocus(dir: Direction): boolean {
  const all = boxes();
  if (all.length === 0) return false;
  const active = document.activeElement as HTMLElement | null;
  const current = all.find((b) => b.el === active);
  if (!current) {
    const preferred = all.find((b) => b.el.hasAttribute("data-nav-default")) ?? all[0];
    preferred.el.focus();
    return true;
  }
  const next = pickNext(current.rect, dir, all.filter((b) => b.el !== current.el));
  if (next) {
    next.focus();
    next.scrollIntoView({ block: "nearest", inline: "nearest" });
    return true;
  }
  return false;
}

/** True when the focused element sits inside a container that handles the
 *  given axis itself (e.g. the manager selector strip owns left/right). */
export function ownedByComponent(dir: Direction): boolean {
  const active = document.activeElement;
  if (!(active instanceof HTMLElement)) return false;
  const owner = active.closest<HTMLElement>("[data-nav-own]");
  if (!owner) return false;
  const axis = owner.dataset.navOwn;
  return axis === "both" || (axis === "horizontal" && (dir === "left" || dir === "right")) || (axis === "vertical" && (dir === "up" || dir === "down"));
}
