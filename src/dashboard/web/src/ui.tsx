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
