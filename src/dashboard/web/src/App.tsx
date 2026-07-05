import { useState } from "react";
import { Health, usePoll } from "./api";
import { TabNav, fmtTime, freshTone } from "./ui";
import { DashboardTab } from "./tabs/DashboardTab";
import { ChartsTab } from "./tabs/ChartsTab";
import { PerformanceTab } from "./tabs/PerformanceTab";
import { MacroTab } from "./tabs/MacroTab";
import { SystemTab } from "./tabs/SystemTab";

const TABS: [string, string][] = [
  ["dashboard", "Dashboard"],
  ["charts", "Charts"],
  ["performance", "Performance"],
  ["macro", "Macro"],
  ["system", "System"],
];

export function App() {
  const [tab, setTab] = useState<string>("dashboard");
  // Health polled at the shell so the top-bar freshness dot is always live.
  const health = usePoll<Health>("/api/health", 30000);

  // Worst freshness across data sources → the global health dot.
  const worst = (health.data?.data_freshness ?? []).reduce<"ok" | "warn" | "bad" | "muted">((acc, d) => {
    const t = freshTone(d.latest);
    const rank = { muted: 0, ok: 1, warn: 2, bad: 3 };
    return rank[t] > rank[acc] ? t : acc;
  }, "ok");

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className={`dot dot-${worst}`} />
          <h1>swing-agent</h1>
          <span className="brand-sub">monitor</span>
        </div>
        <TabNav tabs={TABS} active={tab} onChange={setTab} />
        <span className="clock">
          {health.updated ? `updated ${fmtTime(health.updated.toISOString())}` : "loading…"}
        </span>
      </header>

      <main>
        {tab === "dashboard" && <DashboardTab health={health} />}
        {tab === "charts" && <ChartsTab health={health.data} />}
        {tab === "performance" && <PerformanceTab />}
        {tab === "macro" && <MacroTab />}
        {tab === "system" && <SystemTab />}
      </main>

      <footer>read-only · polls every 30–120s · Postgres-backed · ECharts</footer>
    </div>
  );
}
