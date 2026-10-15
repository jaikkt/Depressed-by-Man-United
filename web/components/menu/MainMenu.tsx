"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Icon } from "@/components/ui/Icon";
import { Logo } from "@/components/ui/Logo";
import { PromptBar } from "@/components/ui/PromptBar";
import { Ticker } from "@/components/ui/Ticker";
import { Tile } from "@/components/ui/Tile";
import { useData } from "@/lib/data";
import { TitleScreen } from "./TitleScreen";
import styles from "./MainMenu.module.css";

const SESSION_KEY = "dbmu-title-seen";

export function MainMenu() {
  const { data } = useData("menu.json");
  // null = not yet known (avoids flashing the title screen for returning visitors)
  const [showTitle, setShowTitle] = useState<boolean | null>(null);

  useEffect(() => {
    let seen = false;
    try {
      seen = window.sessionStorage.getItem(SESSION_KEY) === "1";
    } catch {
      /* storage blocked: just show the title screen */
    }
    // Reading sessionStorage is only possible after mount in a static export.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setShowTitle(!seen);
  }, []);

  const start = () => {
    try {
      window.sessionStorage.setItem(SESSION_KEY, "1");
    } catch {
      /* ignore */
    }
    setShowTitle(false);
  };

  useEffect(() => {
    if (showTitle === false) {
      const first = document.querySelector<HTMLElement>("[data-nav-default]");
      first?.focus();
    }
  }, [showTitle]);

  return (
    <div className={styles.page}>
      <AnimatePresence>{showTitle ? <TitleScreen key="title" onStart={start} /> : null}</AnimatePresence>
      <header className={styles.header}>
        <Logo size={52} withWordmark />
        <span className={styles.season}>{data ? `SEASON ${data.current_season_label}` : ""}</span>
      </header>
      <div className="kit-stripes" />
      <motion.main
        className={styles.hub}
        initial="hidden"
        animate={showTitle === false ? "show" : "hidden"}
        variants={{ hidden: {}, show: { transition: { staggerChildren: 0.05 } } }}
      >
        <motion.div className={styles.hero} variants={item}>
          <Tile href="/managers" label="Manager Eras" kicker="Flagship mode" size="hero" navDefault>
            <div className={`${styles.heroArt} terrace-stripes`}>
              <span className={styles.heroNumber}>{data?.hero_stat ?? "--"}</span>
              <span className={styles.heroCaption}>Average league places vs the squad-value model per season since Ferguson</span>
              <Icon name="manager" size={140} className={styles.heroIcon} />
            </div>
          </Tile>
        </motion.div>
        <motion.div className={styles.sim} variants={item}>
          <Tile href="/simulate" label="Simulate Season" kicker="10,000 seasons" size="wide">
            <div className={styles.tileArt}><Icon name="sim" size={72} /><span className={styles.tileStat}>10K</span></div>
          </Tile>
        </motion.div>
        <motion.div className={styles.fin} variants={item}>
          <Tile href="/finances" label="Club Finances" kicker="Money vs points">
            <div className={styles.tileArt}><Icon name="pound" size={72} /></div>
          </Tile>
        </motion.div>
        <motion.div className={styles.scout} variants={item}>
          <Tile href="/scouting" label="Scouting Report" kicker="Patterns">
            <div className={styles.tileArt}><Icon name="scout" size={72} /></div>
          </Tile>
        </motion.div>
        <motion.div className={styles.transfers} variants={item}>
          <Tile href="/transfers" label="Transfer Market" kicker="Value for money" size="wide">
            <div className={styles.tileArt}><Icon name="transfer" size={72} /><Icon name="boot" size={56} /></div>
          </Tile>
        </motion.div>
        <motion.div className={styles.settings} variants={item}>
          <Tile href="/methodology" label="Settings & Methods" kicker="Sources · Data gaps">
            <div className={styles.tileArt}><Icon name="gear" size={56} /></div>
          </Tile>
        </motion.div>
      </motion.main>
      <div className={styles.ticker}>
        <Ticker items={data?.headlines ?? []} label="HEADLINES" />
      </div>
      <PromptBar prompts={[{ action: "move", label: "Navigate" }, { action: "select", label: "Select mode" }]} />
    </div>
  );
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.2, 0.9, 0.2, 1] as [number, number, number, number] } },
};
