"use client";

import { Fragment, useState, type ReactNode } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { GameShell } from "@/components/ui/GameShell";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { NoData } from "@/components/ui/NoData";
import { Panel } from "@/components/ui/Panel";
import { TabBar } from "@/components/ui/TabBar";
import { useData } from "@/lib/data";
import { useSettings } from "@/lib/settings";
import styles from "./screens.module.css";

type Tab = "settings" | "sources" | "models" | "gaps" | "credits";

export function Methodology() {
  const { data, error } = useData("methodology.json");
  const [tab, setTab] = useState<Tab>("settings");
  const { sounds, setSounds, reducedMotion, setReducedMotion } = useSettings();
  return (
    <GameShell title="Settings" kicker="Methodology" prompts={[{ action: "prevTab", label: "Prev" }, { action: "nextTab", label: "Next" }, { action: "select", label: "Toggle" }, { action: "back", label: "Back" }]}>
      <TabBar value={tab} onChange={setTab} tabs={[{ id: "settings", label: "Settings" }, { id: "sources", label: "Sources" }, { id: "models", label: "Models" }, { id: "gaps", label: "Data Gaps" }, { id: "credits", label: "Credits" }]} />
      <div className={styles.body}>
        {tab === "settings" ? (
          <Panel title="Game settings">
            <div className={styles.toggleRow}>
              <span className={styles.toggleLabel}>UI sounds</span>
              <span style={{ display: "flex", gap: 6 }}>
                <Button active={sounds} variant="secondary" onClick={() => setSounds(true)} navDefault>On</Button>
                <Button active={!sounds} variant="secondary" onClick={() => setSounds(false)}>Off</Button>
              </span>
            </div>
            <div className={styles.toggleRow}>
              <span className={styles.toggleLabel}>Reduced motion</span>
              <span style={{ display: "flex", gap: 6 }}>
                <Button active={reducedMotion} variant="secondary" onClick={() => setReducedMotion(true)}>On</Button>
                <Button active={!reducedMotion} variant="secondary" onClick={() => setReducedMotion(false)}>Off</Button>
              </span>
            </div>
            <p className={styles.note}>Sounds are synthesised in your browser (no audio files) and are off by default. Reduced motion follows your system setting unless changed here.</p>
          </Panel>
        ) : error ? <NoData detail={error} /> : !data ? <LoadingScreen mode="METHODOLOGY" /> : tab === "sources" ? (
          <Panel title="Data sources" kicker={`Generated ${data.generated}`}>
            {data.sources.map((s) => (
              <div key={s.name} className={styles.sourceRow}>
                <div className={styles.sourceName}>
                  <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a>
                  <Badge tone={s.status === "ok" ? "white" : s.status === "partial" ? "outline" : "red"}>{s.status === "ok" ? "OK" : s.status === "partial" ? "Partial" : "Unavailable"}</Badge>
                </div>
                <p className={styles.note}>{s.used_for}. Coverage: {s.coverage}.</p>
              </div>
            ))}
          </Panel>
        ) : tab === "models" ? (
          <div className={styles.grid2}>
            <Panel title="Models">
              {data.models.map((m) => (
                <div key={m.name} className={styles.sourceRow}>
                  <div className={styles.sourceName}>{m.name}</div>
                  <p className={styles.note}>{m.summary}</p>
                </div>
              ))}
            </Panel>
            <Panel title="Assumptions">
              <ul className={styles.prose}>{data.assumptions.map((a) => <li key={a}>{a}</li>)}</ul>
            </Panel>
          </div>
        ) : tab === "gaps" ? (
          <Panel title="Data gaps" kicker="Nothing here was estimated or invented">
            <div className={styles.prose}><Markdown text={data.gaps_markdown} /></div>
          </Panel>
        ) : (
          <Panel title="Image credits" kicker="Wikimedia Commons, free licences only">
            {data.credits.length === 0 ? <NoData detail="No portraits downloaded." /> : data.credits.map((c) => (
              <div key={c.slug} className={styles.sourceRow}>
                <div className={styles.sourceName}>{c.name}</div>
                <p className={styles.note}>
                  <a href={c.source_url} target="_blank" rel="noreferrer" style={{ textDecoration: "underline" }}>{c.title}</a> by {c.author}, licensed {c.license}.
                  Shown with a duotone filter, halftone overlay and angled crop (modified).
                </p>
              </div>
            ))}
            <p className={styles.note}>Managers without a freely licensed photo are shown with stylised initials. No club crests, game logos or copyrighted photos are used.</p>
          </Panel>
        )}
      </div>
    </GameShell>
  );
}

/** Tiny Markdown renderer for DATA_GAPS.md: headings, lists, tables,
 *  paragraphs, **bold**, *italic* and `code`. No raw HTML is ever injected. */
function Markdown({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  const lines = text.split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("# ")) { blocks.push(<h1 key={i}>{inline(line.slice(2))}</h1>); i++; continue; }
    if (line.startsWith("## ")) { blocks.push(<h2 key={i}>{inline(line.slice(3))}</h2>); i++; continue; }
    if (line.startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        const cells = lines[i].split("|").slice(1, -1).map((c) => c.trim());
        if (!cells.every((c) => /^-+$/.test(c))) rows.push(cells);
        i++;
      }
      blocks.push(
        <table key={`t${i}`}><tbody>{rows.map((r, ri) => <tr key={ri}>{r.map((c, ci) => (ri === 0 ? <th key={ci}>{inline(c)}</th> : <td key={ci}>{inline(c)}</td>))}</tr>)}</tbody></table>,
      );
      continue;
    }
    if (line.startsWith("- ")) {
      const items: string[] = [];
      while (i < lines.length && (lines[i].startsWith("- ") || (lines[i].startsWith("  ") && items.length))) {
        if (lines[i].startsWith("- ")) items.push(lines[i].slice(2));
        else items[items.length - 1] += ` ${lines[i].trim()}`;
        i++;
      }
      blocks.push(<ul key={`u${i}`}>{items.map((it, k) => <li key={k}>{inline(it)}</li>)}</ul>);
      continue;
    }
    if (line.trim() === "") { i++; continue; }
    const para: string[] = [];
    while (i < lines.length && lines[i].trim() !== "" && !/^(#|- |\|)/.test(lines[i])) { para.push(lines[i]); i++; }
    blocks.push(<p key={`p${i}`}>{inline(para.join(" "))}</p>);
  }
  return <>{blocks}</>;
}

function inline(s: string): ReactNode {
  const parts = s.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((p, k) => {
    if (p.startsWith("**")) return <strong key={k}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("`")) return <code key={k}>{p.slice(1, -1)}</code>;
    if (p.startsWith("*") && p.length > 2) return <em key={k}>{p.slice(1, -1)}</em>;
    return <Fragment key={k}>{p}</Fragment>;
  });
}
