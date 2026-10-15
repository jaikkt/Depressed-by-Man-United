"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { GameShell } from "@/components/ui/GameShell";
import { Glyph } from "@/components/ui/Glyph";
import { Icon, type IconName } from "@/components/ui/Icon";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { Logo } from "@/components/ui/Logo";
import { NoData } from "@/components/ui/NoData";
import { Panel } from "@/components/ui/Panel";
import { Portrait } from "@/components/ui/Portrait";
import { PromptBar } from "@/components/ui/PromptBar";
import { RadarHex } from "@/components/ui/RadarHex";
import { RatingNumber } from "@/components/ui/RatingNumber";
import { StatBar } from "@/components/ui/StatBar";
import { TabBar } from "@/components/ui/TabBar";
import { Ticker } from "@/components/ui/Ticker";
import { Tile } from "@/components/ui/Tile";
import styles from "./kit.module.css";

const ICONS: IconName[] = ["boot", "whistle", "ball", "pound", "chart", "gear", "trophy", "manager", "scout", "transfer", "sim", "back", "arrow", "pitch", "lock"];
type KitTab = "buttons" | "tiles" | "panels" | "stats" | "misc";

// Component gallery. Uses placeholder labels only: no real statistics appear here.
export default function KitPage() {
  const [tab, setTab] = useState<KitTab>("buttons");
  return (
    <GameShell title="UI Kit" kicker="DEV">
      <TabBar
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "buttons", label: "Buttons" },
          { id: "tiles", label: "Tiles" },
          { id: "panels", label: "Panels" },
          { id: "stats", label: "Stats" },
          { id: "misc", label: "Misc" },
        ]}
      />
      <div className={styles.section}>
        {tab === "buttons" && (
          <>
            <h3 className={styles.h}>States</h3>
            <div className={styles.row}>
              <Button glyph="select" navDefault>Idle</Button>
              <Button glyph="select" forceState="hover">Hover / Focus</Button>
              <Button glyph="select" forceState="pressed">Pressed</Button>
              <Button glyph="select" disabled>Disabled</Button>
            </div>
            <h3 className={styles.h}>Variants</h3>
            <div className={styles.row}>
              <Button>Primary</Button>
              <Button variant="secondary" glyph="back">Secondary</Button>
              <Button variant="ghost">Ghost</Button>
              <Button active>Toggled</Button>
              <Button size="lg" glyph="select">Large</Button>
            </div>
            <h3 className={styles.h}>Glyphs (switch with a gamepad)</h3>
            <div className={styles.row}>
              {(["select", "back", "info", "prevTab", "nextTab", "move"] as const).map((a) => (
                <span key={a} className={styles.glyphCell}><Glyph action={a} /> {a}</span>
              ))}
            </div>
          </>
        )}
        {tab === "tiles" && (
          <div className={styles.tiles}>
            <Tile href="/kit" label="Hero Tile" kicker="Mode" size="hero"><Icon name="manager" size={120} /></Tile>
            <Tile href="/kit" label="Wide Tile" kicker="Mode" size="wide"><Icon name="chart" size={64} /></Tile>
            <Tile href="/kit" label="Focused" kicker="Forced state" forceState="hover"><Icon name="sim" size={64} /></Tile>
            <Tile href="/kit" label="Locked" kicker="Roadmap" locked><Icon name="lock" size={64} /></Tile>
          </div>
        )}
        {tab === "panels" && (
          <div className={styles.grid2}>
            <Panel title="Panel Title" kicker="Kicker"><p>Dark angled panel with a red header strip and top highlight line.</p></Panel>
            <Panel title="Raised" tone="raised" right={<Badge tone="white">Badge</Badge>}><p>Raised tone with header actions.</p></Panel>
            <Panel title="Empty State"><NoData detail="Shown whenever a source could not be found. Numbers are never invented." /></Panel>
            <Panel title="Badges">
              <div className={styles.row}><Badge>Interim</Badge><Badge tone="white">White</Badge><Badge tone="gold">Record</Badge><Badge tone="outline">Outline</Badge></div>
            </Panel>
          </div>
        )}
        {tab === "stats" && (
          <div className={styles.grid2}>
            <Panel title="StatBar">
              <StatBar label="High band" value="85" rating={85} />
              <StatBar label="Mid band" value="65" rating={65} />
              <StatBar label="Low band" value="45" rating={45} />
              <StatBar label="Bad band" value="20" rating={20} />
              <StatBar label="Record" value="99" rating={99} record />
              <StatBar label="Missing" value="--" rating={null} />
            </Panel>
            <Panel title="Rating + Radar">
              <div className={styles.row}>
                <RatingNumber value={88} label="White" />
                <RatingNumber value={54} label="Red" />
                <RatingNumber value={99} label="Gold" tone="gold" size="lg" />
                <RatingNumber value={null} label="None" />
              </div>
              <RadarHex
                axes={[{ label: "Axis A", value: 80 }, { label: "Axis B", value: 55 }, { label: "Axis C", value: 70 }, { label: "Axis D", value: 30 }, { label: "Axis E", value: null }, { label: "Axis F", value: 90 }]}
                compare={[50, 50, 50, 50, 50, 50]}
              />
            </Panel>
          </div>
        )}
        {tab === "misc" && (
          <>
            <h3 className={styles.h}>Icon set</h3>
            <div className={styles.row}>
              {ICONS.map((n) => (
                <span key={n} className={styles.iconCell}><Icon name={n} size={32} /><small>{n}</small></span>
              ))}
            </div>
            <h3 className={styles.h}>Logo</h3>
            <div className={styles.row}><Logo size={80} withWordmark /></div>
            <h3 className={styles.h}>Ticker</h3>
            <Ticker items={["Sample headline one", "Sample headline two", "Sample headline three"]} />
            <h3 className={styles.h}>Portrait fallback</h3>
            <div className={styles.row}><Portrait name="Sample Manager" src={null} /><Portrait name="Sample Manager" src={null} size="sm" /></div>
            <h3 className={styles.h}>Loading screen</h3>
            <div className={styles.loading}><LoadingScreen mode="SAMPLE" tip="This is where a real stat tip appears between modes." /></div>
            <h3 className={styles.h}>Prompt bar (inline copy)</h3>
            <PromptBar inline prompts={[{ action: "select", label: "Select" }, { action: "back", label: "Back" }, { action: "info", label: "Info" }]} />
          </>
        )}
      </div>
    </GameShell>
  );
}
