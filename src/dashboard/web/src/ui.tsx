import { ReactNode } from "react";
import { Row } from "./api";

export function fmtNum(v: unknown, dp = 2): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n.toFixed(dp) : String(v);
}

export function fmtTime(v: unknown): string {
  if (!v) return "—";
  const d = new Date(String(v));
  if (Number.isNaN(d.getTime())) return String(v);
  return d.toISOString().replace("T", " ").slice(0, 16) + "Z";
}

export function ageMinutes(v: unknown): number | null {
  if (!v) return null;
  const d = new Date(String(v));
  if (Number.isNaN(d.getTime())) return null;
  return (Date.now() - d.getTime()) / 60000;
}

export function Section({ title, children, right }: { title: string; children: ReactNode; right?: ReactNode }) {
  return (
    <section className="card">
      <div className="card-head">
        <h2>{title}</h2>
        {right}
      </div>
      {children}
    </section>
  );
}

// Tab nav bar. `tabs` = [key, label]. Controlled by `active`/`onChange`.
export function TabNav({
  tabs,
  active,
  onChange,
}: {
  tabs: [string, string][];
  active: string;
  onChange: (k: string) => void;
}) {
  return (
    <nav className="tabs">
      {tabs.map(([k, label]) => (
        <button
          key={k}
          className={`tab${active === k ? " active" : ""}`}
          onClick={() => onChange(k)}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}

// Big-number hero card for KPI rows.
export function Kpi({
  label,
  value,
  tone,
  sub,
}: {
  label: string;
  value: ReactNode;
  tone?: "pos" | "neg" | "";
  sub?: ReactNode;
}) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${tone ?? ""}`}>{value}</div>
      {sub != null && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

export function Skeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="skeleton">
      {Array.from({ length: rows }).map((_, i) => (
        <div className="skeleton-row" key={i} />
      ))}
    </div>
  );
}

// Age → tone (fresh/warn/stale). thresholds in minutes.
export function freshTone(v: unknown, warnMin = 180, staleMin = 60 * 24): "ok" | "warn" | "bad" | "muted" {
  const a = ageMinutes(v);
  if (a === null) return "muted";
  if (a > staleMin) return "bad";
  if (a > warnMin) return "warn";
  return "ok";
}

export function fmtAge(v: unknown): string {
  const a = ageMinutes(v);
  if (a === null) return "never";
  if (a < 90) return `${Math.round(a)}m`;
  if (a < 60 * 48) return `${Math.round(a / 60)}h`;
  return `${Math.round(a / 1440)}d`;
}

export function Pill({ tone, children }: { tone: "ok" | "warn" | "bad" | "muted"; children: ReactNode }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}

// Generic table. `cols` = [key, header, render?]. Colors r-multiple cells if key ends in _r/r_result.
export function Table({
  rows,
  cols,
}: {
  rows: Row[];
  cols: [string, string, ((v: unknown, row: Row) => ReactNode)?][];
}) {
  if (!rows.length) return <p className="empty">No rows.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{cols.map(([k, h]) => <th key={k}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {cols.map(([k, , render]) => (
                <td key={k}>{render ? render(row[k], row) : rcell(k, row[k])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function rcell(key: string, v: unknown): ReactNode {
  if (key.endsWith("_r") || key === "r_result" || key === "total_r" || key === "avg_r") {
    const n = Number(v);
    if (Number.isFinite(n)) {
      const tone = n > 0 ? "pos" : n < 0 ? "neg" : "";
      return <span className={tone}>{n > 0 ? "+" : ""}{n.toFixed(2)}R</span>;
    }
  }
  return v === null || v === undefined ? "—" : String(v);
}
