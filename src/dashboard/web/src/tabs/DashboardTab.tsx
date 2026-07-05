import { Health, Notifications, Gates, Row, usePoll } from "../api";
import { Section, Table, Pill, Kpi, Skeleton, fmtNum, fmtTime } from "../ui";
import { HealthStrip, Muted, Err, statusPill } from "./shared";

export function DashboardTab({ health }: { health: ReturnType<typeof usePoll<Health>> }) {
  const zones = usePoll<Row[]>("/api/zones", 30000);
  const zonesAtr = usePoll<Row[]>("/api/zones_atr", 30000);
  const trades = usePoll<Row[]>("/api/trades", 30000);
  const notif = usePoll<Notifications>("/api/notifications", 45000);
  const gates = usePoll<Gates>("/api/gates", 120000);

  const openN = zones.data?.length ?? 0;
  const pending = trades.data?.filter((t) => t.status === "PENDING").length ?? 0;
  const filled = trades.data?.filter((t) => t.status === "FILLED").length ?? 0;
  const failedN = notif.data?.counts?.find((c) => c.status === "failed")?.n ?? 0;

  return (
    <>
      <HealthStrip health={health.data} error={health.error} />

      <div className="kpi-row">
        <Kpi label="Open Zones" value={openN} />
        <Kpi label="Live Orders" value={pending} sub="pending" />
        <Kpi label="Filled" value={filled} tone={filled ? "pos" : ""} />
        <Kpi label="Failed Notifs" value={String(failedN)} tone={Number(failedN) ? "neg" : ""} />
      </div>

      <Section title="Open Zones" right={<Muted n={zones.data?.length} />}>
        {zones.error ? <Err msg={zones.error} /> : !zones.data ? <Skeleton /> : (
          <Table
            rows={zones.data}
            cols={[
              ["instrument", "Instr"],
              ["direction", "Dir"],
              ["label", "Label"],
              ["week", "Week"],
              ["zone_bottom", "Zone ↓", (v) => fmtNum(v, 4)],
              ["zone_top", "Zone ↑", (v) => fmtNum(v, 4)],
              ["zone_confluence", "R1", (v) => fmtNum(v, 1)],
              ["status", "Status", (v) => statusPill(v)],
              ["entry", "Entry", (v) => fmtNum(v, 4)],
              ["sl_dist", "SL dist", (v) => fmtNum(v, 4)],
              ["r_result", "R"],
              ["fill_time", "Filled", (v) => (v ? fmtTime(v) : "—")],
            ]}
          />
        )}
      </Section>

      <Section title="Open Zones (ATR SL)" right={<Muted n={zonesAtr.data?.length} />}>
        {zonesAtr.error ? <Err msg={zonesAtr.error} /> : !zonesAtr.data ? <Skeleton /> : (
          <Table
            rows={zonesAtr.data}
            cols={[
              ["instrument", "Instr"],
              ["direction", "Dir"],
              ["label", "Label"],
              ["week", "Week"],
              ["zone_bottom", "Zone ↓", (v) => fmtNum(v, 4)],
              ["zone_top", "Zone ↑", (v) => fmtNum(v, 4)],
              ["zone_confluence", "R1", (v) => fmtNum(v, 1)],
              ["atr_status", "Status", (v) => statusPill(v)],
              ["entry", "Entry", (v) => fmtNum(v, 4)],
              ["sl_dist", "SL dist", (v) => fmtNum(v, 4)],
              ["r_result", "R"],
              ["fill_time", "Filled", (v) => (v ? fmtTime(v) : "—")],
            ]}
          />
        )}
      </Section>

      <Section title="Live Orders (trade_log)" right={<Muted n={trades.data?.length} />}>
        {trades.error ? <Err msg={trades.error} /> : !trades.data ? <Skeleton /> : (
          <Table
            rows={trades.data}
            cols={[
              ["instrument", "Instr"],
              ["direction", "Dir"],
              ["status", "Status", (v) => statusPill(v)],
              ["entry_confluence", "EC", (v) => fmtNum(v, 1)],
              ["limit_price", "Limit", (v) => fmtNum(v, 4)],
              ["sl_price", "SL", (v) => fmtNum(v, 4)],
              ["tp_price", "TP", (v) => fmtNum(v, 4)],
              ["entry_price", "Fill", (v) => fmtNum(v, 4)],
              ["r_result", "R"],
              ["updated_utc", "Updated", (v) => fmtTime(v)],
            ]}
          />
        )}
      </Section>

      <div className="grid">
        <Section title="Upcoming Gates — CB decisions" right={<Muted n={gates.data?.cb?.length} />}>
          {gates.error ? <Err msg={gates.error} /> : !gates.data ? <Skeleton /> : (
            <Table
              rows={gates.data.cb}
              cols={[
                ["decision_date", "Date"],
                ["bank_code", "Bank"],
                ["decision_status", "Status", (v) => statusPill(v)],
                ["hard_block", "Hard-block", (v) => (Array.isArray(v) ? v.join(", ") : String(v ?? "—"))],
              ]}
            />
          )}
        </Section>
        <Section title="Upcoming Gates — Econ (H/M)" right={<Muted n={gates.data?.econ?.length} />}>
          {gates.error ? <Err msg={gates.error} /> : !gates.data ? <Skeleton /> : (
            <Table
              rows={gates.data.econ}
              cols={[
                ["date", "Date"],
                ["time_utc", "UTC"],
                ["country", "Ctry"],
                ["event", "Event"],
                ["impact", "Impact", (v) => <Pill tone={String(v).toUpperCase() === "HIGH" ? "bad" : "warn"}>{String(v)}</Pill>],
              ]}
            />
          )}
        </Section>
      </div>

      <Section title="Notifications" right={<Muted n={notif.data?.recent?.length} />}>
        {notif.error ? <Err msg={notif.error} /> : !notif.data ? <Skeleton /> : (
          <>
            <div className="strip">
              {notif.data.counts.map((c, i) => (
                <div className="chip" key={i}>
                  <span className="chip-k">{String(c.status)}</span>
                  <Pill tone={c.status === "failed" ? "bad" : c.status === "pending" ? "warn" : "ok"}>{String(c.n)}</Pill>
                </div>
              ))}
            </div>
            <Table
              rows={notif.data.recent}
              cols={[
                ["created_utc", "Created", (v) => fmtTime(v)],
                ["event_type", "Type"],
                ["instrument", "Instr"],
                ["title", "Title"],
                ["status", "Status", (v) => statusPill(v)],
                ["error", "Error"],
              ]}
            />
          </>
        )}
      </Section>
    </>
  );
}
