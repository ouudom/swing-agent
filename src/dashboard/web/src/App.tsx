import { Health, Pnl, Row, usePoll } from "./api";
import { Section, Table, Pill, fmtNum, fmtTime, ageMinutes } from "./ui";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function App() {
  const health = usePoll<Health>("/api/health", 30000);
  const zones = usePoll<Row[]>("/api/zones", 30000);
  const pnl = usePoll<Pnl>("/api/pnl", 60000);
  const validations = usePoll<Row[]>("/api/validations", 45000);
  const pipeline = usePoll<Row[]>("/api/pipeline", 30000);

  return (
    <div className="app">
      <header className="topbar">
        <h1>swing-agent · monitor</h1>
        <span className="clock">
          {health.updated ? `updated ${fmtTime(health.updated.toISOString())}` : "loading…"}
        </span>
      </header>

      <HealthStrip health={health.data} error={health.error} />

      <div className="grid">
        <Section title="Open Zones" right={<Muted n={zones.data?.length} />}>
          {zones.error ? <Err msg={zones.error} /> : (
            <Table
              rows={zones.data ?? []}
              cols={[
                ["instrument", "Instr"],
                ["direction", "Dir"],
                ["label", "Label"],
                ["week", "Week"],
                ["zone_bottom", "Zone ↓", (v) => fmtNum(v, 4)],
                ["zone_top", "Zone ↑", (v) => fmtNum(v, 4)],
                ["zone_confluence", "R1", (v) => fmtNum(v, 1)],
                ["latest_verdict", "Verdict", (v) => verdictPill(v)],
                ["entry_confluence", "EC", (v) => fmtNum(v, 1)],
                ["limit_price", "Limit", (v) => fmtNum(v, 4)],
                ["hard_block_flags", "Blocks", (v) => (v ? <Pill tone="bad">{String(v)}</Pill> : "—")],
              ]}
            />
          )}
        </Section>

        <Section title="System P&L (replay)" right={<PnlSummary p={pnl.data} />}>
          {pnl.error ? <Err msg={pnl.error} /> : <PnlChart rows={pnl.data?.by_instrument ?? []} />}
        </Section>
      </div>

      <div className="grid">
        <Section title="Recent Validations" right={<Muted n={validations.data?.length} />}>
          {validations.error ? <Err msg={validations.error} /> : (
            <Table
              rows={validations.data ?? []}
              cols={[
                ["validation_date", "Date"],
                ["instrument", "Instr"],
                ["verdict", "Verdict", (v) => verdictPill(v)],
                ["entry_confluence", "EC", (v) => fmtNum(v, 1)],
                ["limit_price", "Limit", (v) => fmtNum(v, 4)],
                ["hard_block_flags", "Blocks", (v) => (v ? String(v) : "—")],
                ["reason", "Reason"],
              ]}
            />
          )}
        </Section>

        <Section title="Recent Trades (replay)" right={<Muted n={pnl.data?.recent?.length} />}>
          {pnl.error ? <Err msg={pnl.error} /> : (
            <Table
              rows={pnl.data?.recent ?? []}
              cols={[
                ["instrument", "Instr"],
                ["direction", "Dir"],
                ["status", "Status"],
                ["ec_score", "EC", (v) => fmtNum(v, 1)],
                ["r_result", "R"],
                ["mfe_r", "MFE"],
                ["mae_r", "MAE"],
                ["exit_time", "Exit", (v) => fmtTime(v)],
              ]}
            />
          )}
        </Section>
      </div>

      <Section title="Pipeline Runs" right={<Muted n={pipeline.data?.length} />}>
        {pipeline.error ? <Err msg={pipeline.error} /> : (
          <Table
            rows={pipeline.data ?? []}
            cols={[
              ["started_utc", "Started", (v) => fmtTime(v)],
              ["job_name", "Job"],
              ["instrument", "Instr"],
              ["status", "Status", (v) => statusPill(v)],
              ["duration_s", "Dur(s)", (v) => fmtNum(v, 1)],
              ["returncode", "RC", (v) => (Number(v) ? <span className="neg">{String(v)}</span> : "0")],
              ["error", "Error"],
            ]}
          />
        )}
      </Section>

      <footer>read-only · polls every 30–60s · Postgres-backed</footer>
    </div>
  );
}

function HealthStrip({ health, error }: { health: Health | null; error: string | null }) {
  if (error) return <div className="strip"><Err msg={error} /></div>;
  if (!health) return <div className="strip">Loading health…</div>;
  return (
    <div className="strip">
      {health.routines.map((r, i) => {
        const age = ageMinutes(r.last_run_utc);
        const tone = r.status === "error" ? "bad" : age !== null && age > 180 ? "warn" : "ok";
        return (
          <div className="chip" key={i}>
            <span className="chip-k">{String(r.routine_name)}</span>
            <Pill tone={tone}>{String(r.status ?? "?")}</Pill>
            <span className="chip-sub">{age !== null ? `${Math.round(age)}m ago` : "never"}</span>
          </div>
        );
      })}
      {health.jobs.filter((j) => Number(j.returncode) !== 0 && j.returncode != null).map((j, i) => (
        <div className="chip" key={`j${i}`}>
          <span className="chip-k">{String(j.job_name)}</span>
          <Pill tone="bad">rc {String(j.returncode)}</Pill>
        </div>
      ))}
      {health.data_freshness.map((d, i) => {
        const age = ageMinutes(d.latest);
        const tone = age === null ? "muted" : age > 60 * 24 * 3 ? "warn" : "ok";
        return (
          <div className="chip" key={`d${i}`}>
            <span className="chip-k">{String(d.source)}</span>
            <Pill tone={tone}>{age === null ? "—" : `${Math.round(age / 60)}h`}</Pill>
          </div>
        );
      })}
    </div>
  );
}

function PnlSummary({ p }: { p: Pnl | null }) {
  if (!p?.overall) return null;
  const o = p.overall;
  const total = Number(o.total_r ?? 0);
  const resolved = Number(o.resolved ?? 0);
  const wins = Number(o.wins ?? 0);
  const wr = resolved ? Math.round((wins / resolved) * 100) : 0;
  return (
    <span className="summary">
      <b className={total >= 0 ? "pos" : "neg"}>{total >= 0 ? "+" : ""}{total.toFixed(1)}R</b>
      {" · "}{wr}% WR{" · "}n={resolved}
    </span>
  );
}

function PnlChart({ rows }: { rows: Row[] }) {
  if (!rows.length) return <p className="empty">No resolved trades.</p>;
  const data = rows.map((r) => ({ instrument: String(r.instrument), total_r: Number(r.total_r ?? 0) }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(140, data.length * 26)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
        <XAxis type="number" stroke="#8a93a6" fontSize={11} />
        <YAxis type="category" dataKey="instrument" width={64} stroke="#8a93a6" fontSize={11} />
        <Tooltip
          contentStyle={{ background: "#1a1f2b", border: "1px solid #2c3444", fontSize: 12 }}
          formatter={(v: number) => [`${v.toFixed(2)}R`, "total"]}
        />
        <Bar dataKey="total_r">
          {data.map((d, i) => (
            <Cell key={i} fill={d.total_r >= 0 ? "#3fb950" : "#f85149"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

const Muted = ({ n }: { n?: number }) => <span className="muted">{n ?? 0} rows</span>;
const Err = ({ msg }: { msg: string }) => <p className="err">⚠ {msg}</p>;

function verdictPill(v: unknown) {
  const s = String(v ?? "");
  if (!s || s === "null") return "—";
  const tone = s.includes("ORDER") ? "ok" : s.includes("INVALID") ? "bad" : "warn";
  return <Pill tone={tone as "ok" | "bad" | "warn"}>{s}</Pill>;
}

function statusPill(v: unknown) {
  const s = String(v ?? "");
  const tone = s === "ok" || s === "success" ? "ok" : s === "error" ? "bad" : "muted";
  return <Pill tone={tone as "ok" | "bad" | "muted"}>{s || "—"}</Pill>;
}
