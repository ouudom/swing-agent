import { ReactNode, useState } from "react";
import { Pnl, Buckets, Row, ZoneTrades, usePoll } from "../api";
import { Section, Table, TabNav, Kpi, Skeleton, fmtNum, fmtTime } from "../ui";
import { EquityCurve, HBar, MfeMaeScatter } from "../charts";
import { Muted, Err, statusPill } from "./shared";

function wr(row: Row): string {
  const n = Number(row.n ?? 0);
  const wins = Number(row.wins ?? 0);
  return n ? `${Math.round((wins / n) * 100)}%` : "—";
}

const bucketCols: [string, string, ((v: unknown) => ReactNode)?][] = [
  ["bucket", "Bucket", (v) => String(v).replace(/^\d\s/, "")],
  ["n", "n"],
  ["wins", "Wins"],
  ["avg_r", "Avg R", (v) => fmtNum(v, 2)],
  ["total_r", "Total R", (v) => fmtNum(v, 1)],
];

const SUB_TABS: [string, string][] = [
  ["trade_log", "Trade Log"],
  ["trade_replay", "Trade Replay"],
  ["zone_trade", "Zone Trade"],
  ["zone_trade_atr", "Zone Trade (ATR SL)"],
];

export function PerformanceTab() {
  const [sub, setSub] = useState<string>("trade_replay");
  return (
    <>
      <TabNav tabs={SUB_TABS} active={sub} onChange={setSub} />
      {sub === "trade_log" && <TradeLogSubTab />}
      {sub === "trade_replay" && <TradeReplaySubTab />}
      {sub === "zone_trade" && <ZoneTradeSubTab endpoint="/api/zone_trades" title="Zone Trade" />}
      {sub === "zone_trade_atr" && <ZoneTradeSubTab endpoint="/api/zone_trades_atr" title="Zone Trade (ATR SL)" />}
    </>
  );
}

// Real order lifecycle (trade_log) — full history, not just live ones.
function TradeLogSubTab() {
  const trades = usePoll<Row[]>("/api/trades", 30000);
  return (
    <Section title="Trade Log" right={<Muted n={trades.data?.length} />}>
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
            ["exit_price", "Exit", (v) => fmtNum(v, 4)],
            ["r_result", "R"],
            ["hard_block_flags", "Blocks"],
            ["reason", "Reason"],
            ["updated_utc", "Updated", (v) => fmtTime(v)],
          ]}
        />
      )}
    </Section>
  );
}

// Entry-mechanics replay (trade_outcome, R2/EC-gated) — the system's would-be P&L.
function TradeReplaySubTab() {
  const pnl = usePoll<Pnl>("/api/pnl", 60000);
  const equity = usePoll<Row[]>("/api/equity", 60000);
  const buckets = usePoll<Buckets>("/api/buckets", 60000);
  const calib = usePoll<{ zone_outcome: Row[]; trade_outcome: Row[] }>("/api/calibration", 60000);

  const o = pnl.data?.overall;
  const total = Number(o?.total_r ?? 0);
  const resolved = Number(o?.resolved ?? 0);
  const wins = Number(o?.wins ?? 0);
  const winRate = resolved ? Math.round((wins / resolved) * 100) : 0;

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

// Zone-quality replay (zone_outcome or zone_atr_sl_outcome) — no EC, SL source only differs.
function ZoneTradeSubTab({ endpoint, title }: { endpoint: string; title: string }) {
  const zt = usePoll<ZoneTrades>(endpoint, 60000);

  const o = zt.data?.overall;
  const total = Number(o?.total_r ?? 0);
  const resolved = Number(o?.resolved ?? 0);
  const wins = Number(o?.wins ?? 0);
  const winRate = resolved ? Math.round((wins / resolved) * 100) : 0;

  return (
    <>
      <div className="kpi-row">
        <Kpi label="Total R" value={`${total >= 0 ? "+" : ""}${total.toFixed(1)}R`} tone={total >= 0 ? "pos" : "neg"} />
        <Kpi label="Win Rate" value={`${winRate}%`} sub={`${wins}/${resolved}`} />
        <Kpi label="Resolved" value={resolved} />
        <Kpi label="Avg R" value={fmtNum(o?.avg_r, 2)} tone={Number(o?.avg_r) >= 0 ? "pos" : "neg"} />
      </div>

      <Section title="Win-rate by Zone Confluence (R1)">
        {zt.error ? <Err msg={zt.error} /> : !zt.data ? <Skeleton /> : (
          <Table rows={zt.data.by_r1.map((r) => ({ ...r, wr: wr(r) }))} cols={[...bucketCols, ["wr", "WR"]]} />
        )}
      </Section>

      <Section title={`Recent Zone Trades — ${title}`} right={<Muted n={zt.data?.recent?.length} />}>
        {zt.error ? <Err msg={zt.error} /> : !zt.data ? <Skeleton /> : (
          <Table
            rows={zt.data.recent}
            cols={[
              ["instrument", "Instr"],
              ["direction", "Dir"],
              ["label", "Label"],
              ["week", "Week"],
              ["status", "Status", (v) => statusPill(v)],
              ["entry", "Entry", (v) => fmtNum(v, 4)],
              ["sl_dist", "SL dist", (v) => fmtNum(v, 4)],
              ["r_result", "R"],
              ["mfe_r", "MFE"],
              ["mae_r", "MAE"],
              ["fill_time", "Filled", (v) => (v ? fmtTime(v) : "—")],
              ["exit_time", "Exit", (v) => (v ? fmtTime(v) : "—")],
            ]}
          />
        )}
      </Section>
    </>
  );
}
