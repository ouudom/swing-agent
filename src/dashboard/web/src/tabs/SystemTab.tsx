import { useState } from "react";
import { Config, Row, usePoll } from "../api";
import { Section, Table, Skeleton, fmtNum, fmtTime } from "../ui";
import { DocsPanel, Json, Muted, Err, statusPill } from "./shared";

export function SystemTab() {
  const docs = usePoll<Row[]>("/api/docs", 60000);
  const pipeline = usePoll<Row[]>("/api/pipeline", 30000);
  const config = usePoll<Config>("/api/config", 300000);
  const [cfgTab, setCfgTab] = useState<"cb_calendar" | "intervention_watch" | "jawboning">("cb_calendar");

  return (
    <>
      <Section title="Docs (Postgres-served)" right={<Muted n={docs.data?.length} />}>
        {docs.error ? <Err msg={docs.error} /> : !docs.data ? <Skeleton rows={6} /> : <DocsPanel rows={docs.data} />}
      </Section>

      <Section title="Config (JSON)">
        {config.error ? <Err msg={config.error} /> : !config.data ? <Skeleton /> : (
          <>
            <div className="docs-tabs">
              {(["cb_calendar", "intervention_watch", "jawboning"] as const).map((t) => (
                <button key={t} className={`docs-tab${cfgTab === t ? " active" : ""}`} onClick={() => setCfgTab(t)}>{t}</button>
              ))}
            </div>
            <Json value={config.data[cfgTab]} />
          </>
        )}
      </Section>

      <Section title="Pipeline Runs" right={<Muted n={pipeline.data?.length} />}>
        {pipeline.error ? <Err msg={pipeline.error} /> : !pipeline.data ? <Skeleton /> : (
          <Table
            rows={pipeline.data}
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
    </>
  );
}
