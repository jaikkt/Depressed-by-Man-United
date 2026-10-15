// Custom icon set: one 24px grid, one 2px stroke, square caps. Drawn for this
// project so nothing looks like a stock icon pack.

export type IconName =
  | "boot" | "whistle" | "ball" | "pound" | "chart" | "gear" | "trophy"
  | "manager" | "scout" | "transfer" | "sim" | "back" | "arrow" | "pitch" | "lock";

const PATHS: Record<IconName, string> = {
  boot: "M3 7h6l2 5 7 1.5c2 .4 3 1.6 3 3.5v1H3z M3 18h18 M7 18v2 M12 18v2 M17 18v2",
  whistle: "M3 11a5 5 0 1 0 10 0V9h8v4h-5 M8 11h.01 M10 9V6h3",
  ball: "M12 3a9 9 0 1 0 .01 0z M12 8l3.8 2.8-1.5 4.4H9.7L8.2 10.8z M12 8V3.5 M15.8 10.8l4.3-1.4 M14.3 15.2l2.6 3.7 M9.7 15.2l-2.6 3.7 M8.2 10.8 3.9 9.4",
  pound: "M17 7.5A4 4 0 0 0 9.5 6c-.8 1.4-.5 3 0 5 .6 2.4-.2 5-2.5 7h11 M6 12h8",
  chart: "M4 20V4 M4 20h16 M8 16v-5 M12 16V8 M16 16v-7 M20 16v-3",
  gear: "M12 9a3 3 0 1 0 .01 0z M12 2v3 M12 19v3 M2 12h3 M19 12h3 M4.9 4.9 7 7 M17 17l2.1 2.1 M4.9 19.1 7 17 M17 7l2.1-2.1",
  trophy: "M7 4h10v5a5 5 0 0 1-10 0z M7 6H3v2a4 4 0 0 0 4 4 M17 6h4v2a4 4 0 0 1-4 4 M12 14v3 M8 21h8 M9 17h6v4H9z",
  manager: "M12 3a4 4 0 1 0 .01 0z M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8 M9 15l3 3 3-3",
  scout: "M3 14a3.5 3.5 0 1 0 7 0 3.5 3.5 0 1 0-7 0 M14 14a3.5 3.5 0 1 0 7 0 3.5 3.5 0 1 0-7 0 M10 14h4 M5 10.5 7 4h2l1 6 M19 10.5 17 4h-2l-1 6",
  transfer: "M4 8h14l-4-4 M20 16H6l4 4",
  sim: "M5 4l14 8-14 8z",
  back: "M10 6l-6 6 6 6 M4 12h16",
  arrow: "M4 12h16 M14 6l6 6-6 6",
  pitch: "M3 5h18v14H3z M12 5v14 M12 9.5a2.5 2.5 0 1 0 .01 0z M3 9h3v6H3 M21 9h-3v6h3",
  lock: "M6 11h12v10H6z M9 11V8a3 3 0 0 1 6 0v3",
};

export function Icon({ name, size = 24, className, title }: { name: IconName; size?: number; className?: string; title?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="square"
      strokeLinejoin="miter"
      className={className}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
    >
      {title ? <title>{title}</title> : null}
      <path d={PATHS[name]} />
    </svg>
  );
}
