// ECharts chart components (replaces recharts). One shared dark theme, a thin
// echarts-for-react wrapper, and the concrete charts each tab needs.
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { Row } from "./api";
import { fmtDate, fmtTime } from "./ui";

const AXIS = "#8a93a6";
const GRID = "#2c3444";
const UP = "#3fb950";
const DOWN = "#f85149";
const ACCENT = "#4493f8";

const BASE: Partial<EChartsOption> = {
  backgroundColor: "transparent",
  textStyle: { color: "#e6edf3", fontSize: 11 },
  grid: { left: 48, right: 16, top: 24, bottom: 28, containLabel: false },
  tooltip: {
    trigger: "axis",
    backgroundColor: "#1a1f2b",
    borderColor: GRID,
    textStyle: { color: "#e6edf3", fontSize: 12 },
  },
};

function Chart({ option, height = 300 }: { option: EChartsOption; height?: number }) {
  return (
    <ReactECharts
      option={{ ...BASE, ...option }}
      style={{ height, width: "100%" }}
      notMerge
      lazyUpdate
      opts={{ renderer: "canvas" }}
    />
  );
}

// ── Candlestick + volume + zone overlays ────────────────────────────────────
export function Candlestick({ bars, zones, symbol, tf }: { bars: Row[]; zones: Row[]; symbol: string; tf: string }) {
  if (!bars.length) return <p className="empty">No OHLC for {symbol} {tf}.</p>;
  const dates = bars.map((b) => fmtTime(b.datetime));
  const ohlc = bars.map((b) => [Number(b.open), Number(b.close), Number(b.low), Number(b.high)]);
  const vol = bars.map((b) => ({
    value: Number(b.volume ?? 0),
    itemStyle: { color: Number(b.close) >= Number(b.open) ? "rgba(63,185,80,0.4)" : "rgba(248,81,73,0.4)" },
  }));

  // Zone bands + limit/invalidation/tp lines drawn via markArea/markLine on the price series.
  const markAreas = zones
    .filter((z) => z.zone_bottom != null && z.zone_top != null)
    .map((z) => [
      { yAxis: Number(z.zone_bottom), itemStyle: { color: z.direction === "long" ? "rgba(63,185,80,0.08)" : "rgba(248,81,73,0.08)" } },
      { yAxis: Number(z.zone_top) },
    ]);
  const markLines = zones.flatMap((z) => {
    const out: Record<string, unknown>[] = [];
    if (z.limit_price != null) out.push({ yAxis: Number(z.limit_price), lineStyle: { color: ACCENT, type: "dashed" }, label: { formatter: `${z.label ?? ""} limit`, color: ACCENT } });
    if (z.invalidation_level != null) out.push({ yAxis: Number(z.invalidation_level), lineStyle: { color: DOWN, type: "dotted" }, label: { formatter: "inval", color: DOWN } });
    if (z.tp_anchor != null) out.push({ yAxis: Number(z.tp_anchor), lineStyle: { color: UP, type: "dotted" }, label: { formatter: "tp", color: UP } });
    return out;
  });

  const option: EChartsOption = {
    grid: [
      { left: 56, right: 16, top: 16, height: "62%" },
      { left: 56, right: 16, top: "74%", height: "16%" },
    ],
    axisPointer: { link: [{ xAxisIndex: "all" }] },
    tooltip: { trigger: "axis", axisPointer: { type: "cross" }, backgroundColor: "#1a1f2b", borderColor: GRID, textStyle: { color: "#e6edf3", fontSize: 12 } },
    xAxis: [
      { type: "category", data: dates, boundaryGap: true, axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS }, splitLine: { show: false } },
      { type: "category", gridIndex: 1, data: dates, axisLabel: { show: false }, axisLine: { lineStyle: { color: GRID } } },
    ],
    yAxis: [
      { scale: true, axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS }, splitLine: { lineStyle: { color: "#1a2029" } } },
      { gridIndex: 1, scale: true, axisLabel: { show: false }, splitLine: { show: false }, axisLine: { lineStyle: { color: GRID } } },
    ],
    dataZoom: [
      { type: "inside", xAxisIndex: [0, 1], start: 55, end: 100 },
      { type: "slider", xAxisIndex: [0, 1], bottom: 0, height: 16, start: 55, end: 100, borderColor: GRID, fillerColor: "rgba(68,147,248,0.12)" },
    ],
    series: [
      {
        type: "candlestick",
        data: ohlc,
        itemStyle: { color: UP, color0: DOWN, borderColor: UP, borderColor0: DOWN },
        markArea: markAreas.length ? { silent: true, data: markAreas as never } : undefined,
        markLine: markLines.length ? { symbol: "none", data: markLines as never } : undefined,
      },
      { type: "bar", xAxisIndex: 1, yAxisIndex: 1, data: vol },
    ],
  };
  return <Chart option={option} height={420} />;
}

// ── Equity curve (cumulative R) ─────────────────────────────────────────────
export function EquityCurve({ rows }: { rows: Row[] }) {
  if (!rows.length) return <p className="empty">No resolved trades.</p>;
  const data = rows.map((r) => [fmtDate(r.exit_time), Number(r.cum_r ?? 0)]);
  const option: EChartsOption = {
    xAxis: { type: "category", data: data.map((d) => d[0]), axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS } },
    yAxis: { type: "value", name: "cum R", axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS }, splitLine: { lineStyle: { color: "#1a2029" } } },
    series: [
      {
        type: "line",
        data: data.map((d) => d[1]),
        smooth: false,
        showSymbol: false,
        lineStyle: { color: ACCENT, width: 2 },
        areaStyle: { color: "rgba(68,147,248,0.12)" },
        markLine: { symbol: "none", data: [{ yAxis: 0, lineStyle: { color: AXIS, type: "dashed" } }] },
      },
    ],
  };
  return <Chart option={option} height={300} />;
}

// ── Horizontal bar (P&L by instrument) ──────────────────────────────────────
export function HBar({ rows, cat, val, fmt }: { rows: Row[]; cat: string; val: string; fmt?: (n: number) => string }) {
  if (!rows.length) return <p className="empty">No data.</p>;
  const data = rows.map((r) => ({ name: String(r[cat]), value: Number(r[val] ?? 0) }));
  const option: EChartsOption = {
    grid: { left: 72, right: 24, top: 8, bottom: 24 },
    xAxis: { type: "value", axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS }, splitLine: { lineStyle: { color: "#1a2029" } } },
    yAxis: { type: "category", data: data.map((d) => d.name), axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS } },
    tooltip: { trigger: "axis", backgroundColor: "#1a1f2b", borderColor: GRID, valueFormatter: (v) => (fmt ? fmt(Number(v)) : String(v)) },
    series: [
      {
        type: "bar",
        data: data.map((d) => ({ value: d.value, itemStyle: { color: d.value >= 0 ? UP : DOWN } })),
        barMaxWidth: 18,
      },
    ],
  };
  return <Chart option={option} height={Math.max(160, data.length * 28)} />;
}

// ── MFE/MAE scatter (colored by win/loss) ───────────────────────────────────
export function MfeMaeScatter({ rows }: { rows: Row[] }) {
  if (!rows.length) return <p className="empty">No resolved trades.</p>;
  const wins = rows.filter((r) => Number(r.r_result) > 0).map((r) => [Number(r.mae_r), Number(r.mfe_r)]);
  const losses = rows.filter((r) => Number(r.r_result) <= 0).map((r) => [Number(r.mae_r), Number(r.mfe_r)]);
  const option: EChartsOption = {
    xAxis: { type: "value", name: "MAE (R)", axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS }, splitLine: { lineStyle: { color: "#1a2029" } } },
    yAxis: { type: "value", name: "MFE (R)", axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS }, splitLine: { lineStyle: { color: "#1a2029" } } },
    tooltip: { trigger: "item", backgroundColor: "#1a1f2b", borderColor: GRID },
    legend: { textStyle: { color: AXIS }, top: 0 },
    series: [
      { name: "win", type: "scatter", data: wins, symbolSize: 7, itemStyle: { color: UP, opacity: 0.7 } },
      { name: "loss", type: "scatter", data: losses, symbolSize: 7, itemStyle: { color: DOWN, opacity: 0.7 } },
    ],
  };
  return <Chart option={option} height={320} />;
}

// ── Multi-series time line (macro/market series) ────────────────────────────
export function MultiLine({ rows, group, dateKey = "date", valKey = "value" }: { rows: Row[]; group: string; dateKey?: string; valKey?: string }) {
  if (!rows.length) return <p className="empty">No series.</p>;
  const byGroup = new Map<string, [string, number][]>();
  const allDates = new Set<string>();
  for (const r of rows) {
    const g = String(r[group]);
    const d = String(r[dateKey]).slice(0, 10);
    allDates.add(d);
    if (!byGroup.has(g)) byGroup.set(g, []);
    byGroup.get(g)!.push([d, Number(r[valKey])]);
  }
  const dates = Array.from(allDates).sort();
  const series = Array.from(byGroup.entries()).map(([name, pts]) => {
    const m = new Map(pts);
    return { name, type: "line" as const, showSymbol: false, connectNulls: true, data: dates.map((d) => m.get(d) ?? null) };
  });
  const option: EChartsOption = {
    legend: { textStyle: { color: AXIS }, top: 0, type: "scroll" },
    grid: { left: 56, right: 16, top: 32, bottom: 28 },
    xAxis: { type: "category", data: dates, axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS } },
    yAxis: { type: "value", scale: true, axisLine: { lineStyle: { color: GRID } }, axisLabel: { color: AXIS }, splitLine: { lineStyle: { color: "#1a2029" } } },
    series,
  };
  return <Chart option={option} height={300} />;
}
