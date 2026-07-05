import { ReactNode, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Row, Health, getDoc } from "../api";
import { Pill, Table, fmtTime, fmtAge, freshTone, ageMinutes } from "../ui";

export function verdictPill(v: unknown): ReactNode {
  const s = String(v ?? "");
  if (!s || s === "null") return "—";
  const tone = s.includes("ORDER") ? "ok" : s.includes("INVALID") ? "bad" : "warn";
  return <Pill tone={tone as "ok" | "bad" | "warn"}>{s}</Pill>;
}

export function statusPill(v: unknown): ReactNode {
  const s = String(v ?? "");
  const tone =
    s === "ok" || s === "success" || s === "FILLED" ? "ok" :
    s === "error" || s === "failed" ? "bad" :
    s === "PENDING" || s === "pending" ? "warn" : "muted";
  return <Pill tone={tone as "ok" | "bad" | "warn" | "muted"}>{s || "—"}</Pill>;
}

export const Muted = ({ n }: { n?: number }) => <span className="muted">{n ?? 0} rows</span>;
export const Err = ({ msg }: { msg: string }) => <p className="err">⚠ {msg}</p>;

// Health strip — routine chips, failed jobs, per-instrument OHLC freshness.
export function HealthStrip({ health, error }: { health: Health | null; error: string | null }) {
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
            <span className="chip-sub">{fmtAge(r.last_run_utc)} ago</span>
          </div>
        );
      })}
      {health.jobs.filter((j) => Number(j.returncode) !== 0 && j.returncode != null).map((j, i) => (
        <div className="chip" key={`j${i}`}>
          <span className="chip-k">{String(j.job_name)}</span>
          <Pill tone="bad">rc {String(j.returncode)}</Pill>
        </div>
      ))}
    </div>
  );
}

// Reusable prose-doc browser (rulebook / forecast / validation / context).
export function DocsPanel({ rows }: { rows: Row[] }) {
  const [filter, setFilter] = useState<string>("all");
  const [sel, setSel] = useState<Row | null>(null);
  const [body, setBody] = useState<string>("");
  const [busy, setBusy] = useState(false);

  const types = ["all", ...Array.from(new Set(rows.map((r) => String(r.doc_type))))];
  const shown = filter === "all" ? rows : rows.filter((r) => String(r.doc_type) === filter);

  async function open(r: Row) {
    setSel(r);
    setBusy(true);
    setBody("");
    try {
      const d = await getDoc(String(r.doc_type), String(r.doc_key));
      setBody(d ? String(d.body ?? "") : "(not found)");
    } catch (e) {
      setBody(e instanceof Error ? `⚠ ${e.message}` : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!rows.length) return <p className="empty">No docs imported yet.</p>;

  return (
    <div className="docs">
      <div className="docs-tabs">
        {types.map((t) => (
          <button key={t} className={`docs-tab${filter === t ? " active" : ""}`} onClick={() => setFilter(t)}>
            {t}
          </button>
        ))}
      </div>
      <div className="docs-body">
        <div className="docs-list">
          <Table
            rows={shown}
            cols={[
              ["doc_type", "Type"],
              ["doc_key", "Key", (v, row) => <a className="docs-link" onClick={() => open(row)}>{String(v)}</a>],
              ["updated_utc", "Updated", (v) => fmtTime(v)],
            ]}
          />
        </div>
        <div className="docs-view">
          {sel ? (
            <>
              <div className="docs-view-head">
                <b>{String(sel.title || sel.doc_key)}</b>
                <span className="muted">{String(sel.doc_type)} · {String(sel.doc_key)} · v{String(sel.version)}</span>
              </div>
              <div className="docs-md">
                {busy ? "loading…" : <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>}
              </div>
            </>
          ) : (
            <p className="empty">Select a doc to view its body.</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Render an arbitrary object as pretty JSON (config viewers).
export function Json({ value }: { value: unknown }) {
  return <pre className="json">{JSON.stringify(value, null, 2)}</pre>;
}

export { freshTone };
