import { useEffect, useMemo, useState } from "react";
import { Ohlc, Row, usePoll, fetchParam } from "../api";
import { Section, Table, Skeleton, fmtTime } from "../ui";
import { Candlestick } from "../charts";
import { Muted, Err } from "./shared";

export function ChartsTab() {
  const symbols = usePoll<Row[]>("/api/symbols", 300000);
  const quarantine = usePoll<Row[]>("/api/quarantine", 120000);

  const [symbol, setSymbol] = useState<string>("");
  const [tf, setTf] = useState<string>("");
  const [ohlc, setOhlc] = useState<Ohlc | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Distinct symbol list + tfs available for the chosen symbol.
  const syms = useMemo(() => Array.from(new Set((symbols.data ?? []).map((r) => String(r.symbol)))), [symbols.data]);
  const tfs = useMemo(
    () => Array.from(new Set((symbols.data ?? []).filter((r) => String(r.symbol) === symbol).map((r) => String(r.tf)))),
    [symbols.data, symbol],
  );

  // Default selection once the symbol list loads.
  useEffect(() => {
    if (!symbol && syms.length) setSymbol(syms[0]);
  }, [syms, symbol]);
  useEffect(() => {
    if (tfs.length && !tfs.includes(tf)) setTf(tfs.includes("1day") ? "1day" : tfs[0]);
  }, [tfs, tf]);

  // Load candles whenever symbol/tf changes.
  useEffect(() => {
    if (!symbol || !tf) return;
    let live = true;
    setBusy(true);
    setErr(null);
    fetchParam<Ohlc>("/api/ohlc", { symbol, tf })
      .then((d) => live && setOhlc(d))
      .catch((e) => live && setErr(e instanceof Error ? e.message : String(e)))
      .finally(() => live && setBusy(false));
    return () => { live = false; };
  }, [symbol, tf]);

  return (
    <>
      <Section
        title="Candlestick + Zones"
        right={
          <div className="ctrls">
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {syms.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <select value={tf} onChange={(e) => setTf(e.target.value)}>
              {tfs.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        }
      >
        {err ? <Err msg={err} /> : busy || !ohlc ? <Skeleton rows={6} /> : (
          <Candlestick bars={ohlc.bars} zones={ohlc.zones} symbol={symbol} tf={tf} />
        )}
      </Section>

      {ohlc?.zones?.length ? (
        <Section title={`Zones on ${symbol}`} right={<Muted n={ohlc.zones.length} />}>
          <Table
            rows={ohlc.zones}
            cols={[
              ["week", "Week"],
              ["label", "Label"],
              ["direction", "Dir"],
              ["zone_bottom", "↓"],
              ["zone_top", "↑"],
              ["limit_price", "Limit"],
              ["invalidation_level", "Inval"],
              ["tp_anchor", "TP"],
              ["status", "Status"],
            ]}
          />
        </Section>
      ) : null}

      <Section title="Quarantined ticks (provider spikes)" right={<Muted n={quarantine.data?.length} />}>
        {quarantine.error ? <Err msg={quarantine.error} /> : !quarantine.data ? <Skeleton /> : (
          <Table
            rows={quarantine.data}
            cols={[
              ["flagged_utc", "Flagged", (v) => fmtTime(v)],
              ["symbol", "Sym"],
              ["tf", "TF"],
              ["datetime", "Bar", (v) => fmtTime(v)],
              ["action", "Action"],
              ["high", "High"],
              ["low", "Low"],
              ["ref_close", "Ref"],
            ]}
          />
        )}
      </Section>
    </>
  );
}
