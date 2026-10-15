// Formatting helpers. Every function accepts null and returns "NO DATA"-style
// output, because missing values are expected and must never render as 0.

export const NA = "--";

export function money(v: number | null | undefined, digits = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return NA;
  const sign = v < 0 ? "−" : "";
  const a = Math.abs(v);
  if (a >= 1e9) return `${sign}£${(a / 1e9).toFixed(2)}bn`;
  if (a >= 1e6) return `${sign}£${(a / 1e6).toFixed(digits)}m`;
  if (a >= 1e3) return `${sign}£${(a / 1e3).toFixed(0)}k`;
  return `${sign}£${a.toFixed(0)}`;
}

export function pct(v: number | null | undefined, digits = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return NA;
  return `${(v * 100).toFixed(digits)}%`;
}

export function num(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return NA;
  return v.toFixed(digits);
}

export function signed(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return NA;
  const s = v.toFixed(digits);
  if (Number(s) === 0) return (0).toFixed(digits); // avoid "−0.0" for tiny negatives
  return v > 0 ? `+${s}` : s.replace("-", "−");
}

export function ordinal(n: number | null | undefined): string {
  if (n === null || n === undefined) return NA;
  const s = ["TH", "ST", "ND", "RD"];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] ?? s[v] ?? s[0]}`;
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "PRESENT";
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString("en-GB", { month: "short", year: "numeric" }).toUpperCase();
}

export function year(iso: string | null | undefined): string {
  return iso ? iso.slice(0, 4) : "NOW";
}

export const TEAM_COLORS: Record<string, string> = {
  "manchester-united": "var(--red)",
  "manchester-city": "#9FB8C9",
  liverpool: "#C9C4BA",
  arsenal: "#E8E2D4",
  chelsea: "#6E7F99",
  tottenham: "#8A8A90",
};

const TEAM_NAMES: Record<string, string> = {
  "manchester-united": "Man United",
  "manchester-city": "Man City",
  liverpool: "Liverpool",
  arsenal: "Arsenal",
  chelsea: "Chelsea",
  tottenham: "Tottenham",
};

export function teamName(slug: string): string {
  return TEAM_NAMES[slug] ?? slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
