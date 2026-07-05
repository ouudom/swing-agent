import { ReactNode, useMemo, useState } from "react";
import { Row } from "./api";

export const DISPLAY_TIME_ZONE = "Asia/Phnom_Penh";

export function fmtNum(v: unknown, dp = 2): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n.toFixed(dp) : String(v);
}

function parseTime(v: unknown): Date | null {
  if (!v) return null;
  if (v instanceof Date) return Number.isNaN(v.getTime()) ? null : v;
  const s = String(v);
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(s);
  const normalized = /^\d{4}-\d{2}-\d{2}$/.test(s) || hasZone ? s : `${s}Z`;
  const d = new Date(normalized);
  return Number.isNaN(d.getTime()) ? null : d;
}

function partsInDisplayZone(d: Date): Record<string, string> {
  return Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: DISPLAY_TIME_ZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).formatToParts(d).map((p) => [p.type, p.value]),
  );
}

export function fmtTime(v: unknown): string {
  const d = parseTime(v);
  if (!d) return v ? String(v) : "—";
  const p = partsInDisplayZone(d);
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute} ICT`;
}

export function fmtDate(v: unknown): string {
  const d = parseTime(v);
  if (!d) return v ? String(v) : "—";
  const p = partsInDisplayZone(d);
  return `${p.year}-${p.month}-${p.day}`;
}

export function fmtUtcDateTimeParts(date: unknown, timeUtc: unknown): string {
  if (!date || !timeUtc) return "—";
  const time = String(timeUtc);
  if (!/^\d{1,2}:\d{2}/.test(time)) return time;
  return fmtTime(`${String(date).slice(0, 10)}T${time}Z`);
}

export function fmtUtcDateParts(date: unknown, timeUtc: unknown): string {
  if (!date) return "—";
  const time = String(timeUtc ?? "00:00");
  if (!/^\d{1,2}:\d{2}/.test(time)) return String(date).slice(0, 10);
  return fmtDate(`${String(date).slice(0, 10)}T${time}Z`);
}

export function ageMinutes(v: unknown): number | null {
  const d = parseTime(v);
  if (!d) return null;
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
  interactive = false,
  filterKeys = [],
}: {
  rows: Row[];
  cols: [string, string, ((v: unknown, row: Row) => ReactNode)?][];
  interactive?: boolean;
  filterKeys?: string[];
}) {
  const defaultSort = useMemo(() => {
    const keys = cols.map(([k]) => k);
    return keys.includes("fill_time") ? "fill_time" : "";
  }, [cols]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sortKey, setSortKey] = useState(defaultSort);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const filterOptions = useMemo(() => {
    return Object.fromEntries(filterKeys.map((key) => [
      key,
      Array.from(new Set(rows.map((row) => String(row[key] ?? "")).filter(Boolean))).sort(),
    ]));
  }, [filterKeys, rows]);

  const shown = useMemo(() => {
    const filtered = interactive
      ? rows.filter((row) => Object.entries(filters).every(([key, value]) => !value || String(row[key] ?? "") === value))
      : rows;
    const sorted = interactive && sortKey
      ? [...filtered].sort((a, b) => compareValues(a[sortKey], b[sortKey], sortDir))
      : filtered;
    return sorted;
  }, [rows, filters, interactive, sortKey, sortDir]);

  const pages = Math.max(1, Math.ceil(shown.length / pageSize));
  const safePage = Math.min(page, pages);
  const pageRows = interactive ? shown.slice((safePage - 1) * pageSize, safePage * pageSize) : shown;

  if (!rows.length) return <p className="empty">No rows.</p>;
  return (
    <>
      {interactive ? (
        <div className="table-tools">
          <div className="table-filters">
            {filterKeys.map((key) => {
              const label = cols.find(([k]) => k === key)?.[1] ?? key;
              return (
                <select
                  key={key}
                  value={filters[key] ?? ""}
                  onChange={(e) => {
                    setFilters((prev) => ({ ...prev, [key]: e.target.value }));
                    setPage(1);
                  }}
                >
                  <option value="">{label}: All</option>
                  {(filterOptions[key] ?? []).map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              );
            })}
          </div>
          <span className="muted">{shown.length}/{rows.length} rows</span>
        </div>
      ) : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {cols.map(([k, h]) => (
                <th key={k}>
                  {interactive ? (
                    <button
                      className="th-sort"
                      onClick={() => {
                        setPage(1);
                        if (sortKey === k) setSortDir(sortDir === "asc" ? "desc" : "asc");
                        else { setSortKey(k); setSortDir(k === "fill_time" ? "desc" : "asc"); }
                      }}
                    >
                      {h}{sortKey === k ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                    </button>
                  ) : h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i}>
                {cols.map(([k, , render]) => (
                  <td key={k}>{render ? render(row[k], row) : rcell(k, row[k])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {interactive ? (
        <div className="table-pager">
          <button disabled={safePage <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</button>
          <span className="muted">Page {safePage}/{pages}</span>
          <button disabled={safePage >= pages} onClick={() => setPage((p) => Math.min(pages, p + 1))}>Next</button>
        </div>
      ) : null}
    </>
  );
}

function compareValues(a: unknown, b: unknown, dir: "asc" | "desc"): number {
  const av = sortValue(a);
  const bv = sortValue(b);
  let out = 0;
  if (typeof av === "number" && typeof bv === "number") out = av - bv;
  else out = String(av).localeCompare(String(bv));
  return dir === "asc" ? out : -out;
}

function sortValue(v: unknown): number | string {
  if (v === null || v === undefined || v === "") return "";
  const n = Number(v);
  if (Number.isFinite(n) && String(v).trim() !== "") return n;
  const t = Date.parse(String(v));
  if (Number.isFinite(t)) return t;
  return String(v).toLowerCase();
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
