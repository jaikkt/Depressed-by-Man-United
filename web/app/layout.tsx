import type { Metadata } from "next";
import { Barlow, Saira_Condensed } from "next/font/google";
import type { ReactNode } from "react";
import { Floodlights } from "@/components/ui/Floodlights";
import { NavRoot } from "@/components/ui/NavRoot";
import { InputProvider } from "@/lib/input";
import { SettingsProvider } from "@/lib/settings";
import "./globals.css";

// next/font downloads these at build time and self-hosts them: no runtime
// requests to Google, and no layout shift.
const saira = Saira_Condensed({ subsets: ["latin"], weight: ["500", "600", "700", "800"], variable: "--font-saira", display: "swap" });
const barlow = Barlow({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-barlow", display: "swap" });

export const metadata: Metadata = {
  title: "DepressedByManUTD",
  description: "How badly have Manchester United underperformed their money? A data study in the style of a football game menu.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${saira.variable} ${barlow.variable}`}>
      <body>
        <div className="bg-brick" aria-hidden />
        <Floodlights />
        <div className="bg-grain" aria-hidden />
        <SettingsProvider>
          <InputProvider>
            <NavRoot />
            {children}
          </InputProvider>
        </SettingsProvider>
      </body>
    </html>
  );
}
