import { useEffect, useMemo, useState } from "react";
import { Health, Ohlc, Row, usePoll, fetchParam } from "../api";
import { Section, Table, Skeleton, Pill, fmtAge, fmtTime, freshTone } from "../ui";
import { Candlestick } from "../charts";
import { Muted, Err } from "./shared";

const INSTRUMENTS = [
  "xauusd",
  "eurusd",
  "gbpusd",
  "eurgbp",
  "audusd",
  "nzdusd",
  "usdcad",
  "usdchf",
  "usdjpy",
  "eurjpy",
  "gbpjpy",
];
const DEFAULT_TFS = ["15min", "1h", "4h", "1day"];

function latestWeekZones(zones: Row[]): Row[] {
  const weeks = zones.map((z) => String(z.week ?? "")).filter(Boolean);
  if (!weeks.length) return zones;
  const sortedWeeks = weeks.sort();
  const latestWeek = sortedWeeks[sortedWeeks.length - 1];
  return zones.filter((z) => String(z.week ?? "") === latestWeek);
}

export function ChartsTab({ health }: { health: Health | null }) {
  const quarantine = usePoll<Row[]>("/api/quarantine", 120000);

  const [symbol, setSymbol] = useState<string>("");
  const [ohlcByTf, setOhlcByTf] = useState<Record<string, Ohlc | null>>({});
  const [errByTf, setErrByTf] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const syms = INSTRUMENTS;
  const selectedFreshness = useMemo(
    () => (health?.ohlc_freshness ?? []).filter((f) => String(f.symbol) === symbol),
    [health?.ohlc_freshness, symbol],
  );
  const freshestOhlc = useMemo(() => {
    return selectedFreshness.reduce<Row | null>((freshest, row) => {
      if (!freshest) return row;
      return new Date(String(row.latest)).getTime() > new Date(String(freshest.latest)).getTime() ? row : freshest;
    }, null);
  }, [selectedFreshness]);
  const latestZones = useMemo(() => {
    const source = DEFAULT_TFS.map((tf) => ohlcByTf[tf]?.zones ?? []).find((zones) => zones.length) ?? [];
    return latestWeekZones(source);
  }, [ohlcByTf]);

  useEffect(() => {
    if (!symbol && syms.length) setSymbol(syms[0]);
  }, [syms, symbol]);

  // Load all chart timeframes whenever the selected instrument changes.
  useEffect(() => {
    if (!symbol) return;
    let live = true;
    setBusy(true);
    setOhlcByTf({});
    setErrByTf({});
    Promise.all(
      DEFAULT_TFS.map(async (tf) => {
        try {
          const data = await fetchParam<Ohlc>("/api/ohlc", { symbol, tf });
          return { tf, data, error: null };
        } catch (e) {
          return { tf, data: null, error: e instanceof Error ? e.message : String(e) };
        }
      }),
    ).then((results) => {
      if (!live) return;
      setOhlcByTf(Object.fromEntries(results.map((r) => [r.tf, r.data])));
      setErrByTf(Object.fromEntries(results.filter((r) => r.error).map((r) => [r.tf, r.error ?? ""])));
    }).finally(() => live && setBusy(false));
    return () => { live = false; };
  }, [symbol]);

  return (
    <>
      <div className="chart-symbol-top">
        <div className="symbol-tabs">
          {syms.map((s) => (
            <button
              key={s}
              className={`symbol-tab${symbol === s ? " active" : ""}`}
              onClick={() => setSymbol(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <Section title="OHLC Data Freshness">
        {freshestOhlc ? (
          <div className="fresh-strip fresh-strip-panel">
            <div className="chip chip-sm">
              <span className="chip-k">{symbol}</span>
              <Pill tone={freshTone(freshestOhlc.latest)}>{fmtAge(freshestOhlc.latest)}</Pill>
            </div>
          </div>
        ) : (
          <p className="empty">No OHLC rows.</p>
        )}
      </Section>

      {DEFAULT_TFS.map((tf) => {
        const ohlc = ohlcByTf[tf];
        const err = errByTf[tf];
        return (
          <Section key={tf} title={`${tf} Candlestick + Zones`} right={<span className="muted">{symbol.toUpperCase()}</span>}>
            {err ? <Err msg={err} /> : busy || !ohlc ? <Skeleton rows={6} /> : (
              <Candlestick bars={ohlc.bars} zones={latestZones} symbol={symbol} tf={tf} height={360} />
            )}
          </Section>
        );
      })}

      {latestZones.length ? (
        <Section title={`Latest-week zones on ${symbol}`} right={<Muted n={latestZones.length} />}>
          <Table
            rows={latestZones}
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
