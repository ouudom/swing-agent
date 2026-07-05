import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Macro, Row, usePoll } from "../api";
import { Section, Table, Skeleton, fmtTime } from "../ui";
import { MultiLine } from "../charts";
import { Muted, Err } from "./shared";

export function MacroTab() {
  const macro = usePoll<Macro>("/api/macro", 300000);
  const news = usePoll<Row[]>("/api/news", 120000);

  return (
    <>
      <Section title="Yield Environment" right={macro.data?.yield_env ? <span className="muted">updated {fmtTime(macro.data.yield_env.updated_utc)}</span> : null}>
        {macro.error ? <Err msg={macro.error} /> : !macro.data ? <Skeleton rows={6} /> : macro.data.yield_env ? (
          <div className="docs-md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(macro.data.yield_env.body ?? "")}</ReactMarkdown>
          </div>
        ) : <p className="empty">No yield_environment doc.</p>}
      </Section>

      <div className="grid">
        <Section title="Macro series (FRED)">
          {!macro.data ? <Skeleton /> : <MultiLine rows={macro.data.macro_series} group="series_id" />}
        </Section>
        <Section title="Market series">
          {!macro.data ? <Skeleton /> : <MultiLine rows={macro.data.market_series} group="symbol" />}
        </Section>
      </div>

      <div className="grid">
        <Section title="COT — net positioning" right={<Muted n={macro.data?.cot?.length} />}>
          {!macro.data ? <Skeleton /> : <MultiLine rows={macro.data.cot} group="contract" valKey="net" />}
        </Section>
        <Section title="GLD holdings (tonnes)">
          {!macro.data ? <Skeleton /> : <MultiLine rows={macro.data.gld.map((r) => ({ ...r, series: "tonnes" }))} group="series" valKey="tonnes" />}
        </Section>
      </div>

      <Section title="News" right={<Muted n={news.data?.length} />}>
        {news.error ? <Err msg={news.error} /> : !news.data ? <Skeleton /> : (
          <Table
            rows={news.data}
            cols={[
              ["datetime_utc", "When", (v) => fmtTime(v)],
              ["category", "Cat"],
              ["headline", "Headline", (v, row) => (row.url ? <a href={String(row.url)} target="_blank" rel="noreferrer">{String(v)}</a> : String(v))],
              ["source", "Source"],
              ["related", "Related"],
            ]}
          />
        )}
      </Section>
    </>
  );
}
