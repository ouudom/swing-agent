import { ReactNode } from "react";
import { Pnl, Buckets, Row, usePoll } from "../api";
import { Section, Table, Kpi, Skeleton, fmtNum, fmtTime } from "../ui";
import { EquityCurve, HBar, MfeMaeScatter } from "../charts";
import { Muted, Err } from "./shared";

function wr(row: Row): string {
  const n = Number(row.n ?? 0);
  const wins = Number(row.wins ?? 0);
  return n ? `${Math.round((wins / n) * 100)}%` : "—";
}

export function PerformanceTab() {
  const pnl = usePoll<Pnl>("/api/pnl", 60000);
  const equity = usePoll<Row[]>("/api/equity", 60000);
  const buckets = usePoll<Buckets>("/api/buckets", 60000);
  const calib = usePoll<{ zone_outcome: Row[]; trade_outcome: Row[] }>("/api/calibration", 60000);

  const o = pnl.data?.overall;
  const total = Number(o?.total_r ?? 0);
  const resolved = Number(o?.resolved ?? 0);
  const wins = Number(o?.wins ?? 0);
  const winRate = resolved ? Math.round((wins / resolved) * 100) : 0;

  const bucketCols: [string, string, ((v: unknown) => ReactNode)?][] = [
    ["bucket", "Bucket", (v) => String(v).replace(/^\d\s/, "")],
    ["n", "n"],
    ["wins", "Wins"],
    ["avg_r", "Avg R", (v) => fmtNum(v, 2)],
    ["total_r", "Total R", (v) => fmtNum(v, 1)],
  ];

  return (
    <>
      <div className="kpi-row">
        <Kpi label="Total R" value={`${total >= 0 ? "+" : ""}${total.toFixed(1)}R`} tone={total >= 0 ? "pos" : "neg"} />
        <Kpi label="Win Rate" value={`${winRate}%`} sub={`${wins}/${resolved}`} />
        <Kpi label="Resolved" value={resolved} />
        <Kpi label="Avg R" value={fmtNum(o?.avg_r, 2)} tone={Number(o?.avg_r) >= 0 ? "pos" : "neg"} />
      </div>

      <Section title="Equity Curve (cumulative R)">
        {equity.error ? <Err msg={equity.error} /> : !equity.data ? <Skeleton rows={6} /> : <EquityCurve rows={equity.data} />}
      </Section>

      <div className="grid">
        <Section title="P&L by Instrument">
          {pnl.error ? <Err msg={pnl.error} /> : !pnl.data ? <Skeleton /> : (
            <HBar rows={pnl.data.by_instrument} cat="instrument" val="total_r" fmt={(n) => `${n.toFixed(2)}R`} />
          )}
        </Section>
        <Section title="MFE / MAE scatter">
          {buckets.error ? <Err msg={buckets.error} /> : !buckets.data ? <Skeleton /> : <MfeMaeScatter rows={buckets.data.scatter} />}
        </Section>
      </div>

      <div className="grid">
        <Section title="Win-rate by Entry Confluence (R2)" right={<span className="muted">is the gate earning its keep?</span>}>
          {buckets.error ? <Err msg={buckets.error} /> : !buckets.data ? <Skeleton /> : (
            <Table rows={buckets.data.ec.map((r) => ({ ...r, wr: wr(r) }))} cols={[...bucketCols, ["wr", "WR"]]} />
          )}
        </Section>
        <Section title="Win-rate by Zone Confluence (R1)">
          {buckets.error ? <Err msg={buckets.error} /> : !buckets.data ? <Skeleton /> : (
            <Table rows={buckets.data.r1.map((r) => ({ ...r, wr: wr(r) }))} cols={[...bucketCols, ["wr", "WR"]]} />
          )}
        </Section>
      </div>

      <div className="grid">
        <Section title="By Conviction">
          {buckets.error ? <Err msg={buckets.error} /> : !buckets.data ? <Skeleton /> : (
            <Table
              rows={buckets.data.conviction.map((r) => ({ ...r, wr: wr(r) }))}
              cols={[["conviction", "Conv"], ["n", "n"], ["wr", "WR"], ["avg_r", "Avg R", (v) => fmtNum(v, 2)], ["total_r", "Total R", (v) => fmtNum(v, 1)]]}
            />
          )}
        </Section>
        <Section title="Gate-accuracy audit" right={<span className="muted">were blocks correct?</span>}>
          {buckets.error ? <Err msg={buckets.error} /> : !buckets.data ? <Skeleton /> : (
            <Table
              rows={buckets.data.gate}
              cols={[["block_verdict", "Verdict"], ["block_flags", "Flags"], ["n", "n"], ["avg_r", "Avg R", (v) => fmtNum(v, 2)]]}
            />
          )}
        </Section>
      </div>

      <Section title="Recent Trades (replay)" right={<Muted n={pnl.data?.recent?.length} />}>
        {pnl.error ? <Err msg={pnl.error} /> : !pnl.data ? <Skeleton /> : (
          <Table
            rows={pnl.data.recent}
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

      <Section title="Calibration — trade_outcome (R2)" right={<Muted n={calib.data?.trade_outcome?.length} />}>
        {calib.error ? <Err msg={calib.error} /> : !calib.data ? <Skeleton /> : (
          <Table
            rows={calib.data.trade_outcome}
            cols={[["instrument", "Instr"], ["direction", "Dir"], ["status", "Status"], ["n", "n"], ["avg_r", "Avg R", (v) => fmtNum(v, 2)]]}
          />
        )}
      </Section>
    </>
  );
}
