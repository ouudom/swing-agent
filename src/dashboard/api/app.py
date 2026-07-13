"""app.py — FastAPI port of server.py (read-only monitoring dashboard).

Same endpoints, same SQL, same ACTIVE_INSTRUMENTS filter, same static-bundle-serving
behavior as the original `http.server` implementation. Ports to a real framework
(async, typed routes, docs at /docs) without changing any query or response shape —
every `api_*`/`query()` function below is a straight copy from server.py.

server.py is kept alongside for rollback; swap the Dockerfile CMD back to
`python api/server.py` to revert.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.getenv("DASHBOARD_PORT", "8888"))
# Dashboard-wide instrument filter — other 9 pairs stay in Postgres (dead history) but
# never surface in any tab. Keep in sync with engine.commands.ACTIVE_INSTRUMENTS.
ACTIVE_INSTRUMENTS = ["xauusd", "eurusd", "usdchf"]
DIST_DIR = Path(os.getenv("DASHBOARD_DIST", Path(__file__).resolve().parent / "static"))
ROW_CAP = 500
SQL_TIMEOUT_MS = 8000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def pg_connect():
    import psycopg

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg.connect(dsn)
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "swing_agent"),
        user=os.getenv("POSTGRES_USER", "swing_agent"),
        password=os.getenv("POSTGRES_PASSWORD", "swing_agent_dev_password"),
    )


def _norm(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def query(sql: str, params=()):
    with pg_connect() as con:
        with con.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {SQL_TIMEOUT_MS}")
            cur.execute(sql, params)
            cols = [d.name for d in cur.description]
            rows = cur.fetchmany(ROW_CAP)
    return [{cols[i]: _norm(v) for i, v in enumerate(row)} for row in rows]


# ---------------------------------------------------------------------------
# Query functions — identical SQL to server.py.
# ---------------------------------------------------------------------------

def api_health():
    return {
        "routines": query(
            "SELECT routine_name, status, last_run_utc, branch, commit_sha, notes, updated_utc "
            "FROM routine_checkpoint ORDER BY routine_name"
        ),
        "jobs": query(
            "SELECT DISTINCT ON (job_name) job_name, instrument, status, started_utc, "
            "finished_utc, duration_s, returncode "
            "FROM pipeline_run ORDER BY job_name, started_utc DESC"
        ),
        "data_freshness": query(
            "SELECT 'ohlc' AS source, MAX(datetime) AS latest FROM ohlc WHERE symbol = ANY(%s) "
            "UNION ALL SELECT 'news', MAX(datetime_utc) FROM news "
            "UNION ALL SELECT 'econ_calendar', MAX(date)::timestamptz FROM econ_calendar",
            (ACTIVE_INSTRUMENTS,),
        ),
        "ohlc_freshness": query(
            "SELECT symbol, tf, MAX(datetime) AS latest, COUNT(*) AS bars "
            "FROM ohlc WHERE symbol = ANY(%s) GROUP BY symbol, tf ORDER BY symbol, tf",
            (ACTIVE_INSTRUMENTS,),
        ),
        "server_time": utc_now(),
    }


def api_trades():
    return query(
        "SELECT zone_id, instrument, week, label, direction, status, entry_confluence, "
        "limit_price, sl_price, tp_price, entry_price, fill_time, exit_price, exit_time, "
        "r_result, hard_block_flags, reason, validation_date, updated_utc "
        "FROM trade_log WHERE instrument = ANY(%s) ORDER BY "
        "CASE status WHEN 'FILLED' THEN 0 WHEN 'PENDING' THEN 1 ELSE 2 END, "
        "updated_utc DESC LIMIT 100",
        (ACTIVE_INSTRUMENTS,),
    )


def api_notifications():
    counts = query(
        "SELECT status, COUNT(*) AS n FROM notification_event "
        "WHERE instrument IS NULL OR instrument = ANY(%s) GROUP BY status ORDER BY status",
        (ACTIVE_INSTRUMENTS,),
    )
    recent = query(
        "SELECT event_id, event_type, instrument, zone_id, title, message, status, "
        "created_utc, sent_utc, error FROM notification_event "
        "WHERE instrument IS NULL OR instrument = ANY(%s) "
        "ORDER BY created_utc DESC LIMIT 40",
        (ACTIVE_INSTRUMENTS,),
    )
    return {"counts": counts, "recent": recent}


def api_gates():
    return {
        "cb": query(
            "SELECT bank_code, name, hard_block, caution, time_note, "
            "(d->>'date')::date AS decision_date, d->>'status' AS decision_status "
            "FROM cb_calendar, jsonb_array_elements(dates) AS d "
            "WHERE (d->>'date')::date >= date_trunc('week', now() AT TIME ZONE 'utc')::date "
            "AND (d->>'date')::date < date_trunc('week', now() AT TIME ZONE 'utc')::date + 14 "
            "ORDER BY decision_date LIMIT 30"
        ),
        "econ": query(
            "SELECT date, time_utc, country, event, impact, estimate, actual, prev "
            "FROM econ_calendar "
            "WHERE date >= date_trunc('week', now() AT TIME ZONE 'utc')::date "
            "AND date < date_trunc('week', now() AT TIME ZONE 'utc')::date + 14 "
            "AND upper(coalesce(impact,'')) IN ('HIGH','MEDIUM') "
            "ORDER BY date, time_utc LIMIT 60"
        ),
        "intervention": query(
            "SELECT pair, intervention_level, caution_band, regime, verified_through "
            "FROM intervention_watch ORDER BY pair"
        ),
    }


def api_ohlc(symbol: str, tf: str):
    rows = query(
        "SELECT datetime, open, high, low, close, volume FROM ohlc "
        "WHERE symbol = %s AND tf = %s ORDER BY datetime DESC LIMIT 300",
        (symbol, tf),
    )
    rows.reverse()
    zones = query(
        "SELECT zone_id, week, label, direction, zone_bottom, zone_top, status, "
        "limit_price, invalidation_level, tp_anchor, published_utc "
        "FROM zone_ledger WHERE instrument = %s ORDER BY published_utc DESC LIMIT 12",
        (symbol,),
    )
    return {"symbol": symbol, "tf": tf, "bars": rows, "zones": zones}


def api_symbols():
    return query(
        "SELECT DISTINCT symbol, tf FROM ohlc WHERE symbol = ANY(%s) ORDER BY symbol, tf",
        (ACTIVE_INSTRUMENTS,),
    )


def api_quarantine():
    return query(
        "SELECT symbol, tf, datetime, action, open, high, low, close, ref_close, flagged_utc "
        "FROM ohlc_quarantine WHERE symbol = ANY(%s) "
        "ORDER BY flagged_utc DESC NULLS LAST, datetime DESC LIMIT 100",
        (ACTIVE_INSTRUMENTS,),
    )


def api_equity():
    return query(
        "SELECT zone_id, instrument, direction, exit_time, r_result, "
        "SUM(r_result) OVER (ORDER BY exit_time, resolved_utc) AS cum_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND exit_time IS NOT NULL "
        "AND instrument = ANY(%s) "
        "ORDER BY exit_time, resolved_utc",
        (ACTIVE_INSTRUMENTS,),
    )


def api_buckets():
    ec = query(
        "SELECT CASE WHEN ec_score < 5 THEN '0 <5' WHEN ec_score < 6 THEN '1 5-6' "
        "WHEN ec_score < 7 THEN '2 6-7' WHEN ec_score < 8 THEN '3 7-8' ELSE '4 8+' END AS bucket, "
        "COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND instrument = ANY(%s) GROUP BY 1 ORDER BY 1",
        (ACTIVE_INSTRUMENTS,),
    )
    r1 = query(
        "SELECT CASE WHEN zone_confluence < 6 THEN '0 <6' WHEN zone_confluence < 7 THEN '1 6-7' "
        "WHEN zone_confluence < 8 THEN '2 7-8' WHEN zone_confluence < 9 THEN '3 8-9' ELSE '4 9+' END AS bucket, "
        "COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND instrument = ANY(%s) GROUP BY 1 ORDER BY 1",
        (ACTIVE_INSTRUMENTS,),
    )
    conviction = query(
        "SELECT conviction, COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND instrument = ANY(%s) "
        "GROUP BY conviction ORDER BY conviction",
        (ACTIVE_INSTRUMENTS,),
    )
    gate = query(
        "SELECT block_verdict, block_flags, COUNT(*) AS n, AVG(r_result) AS avg_r "
        "FROM trade_outcome WHERE block_verdict IS NOT NULL AND instrument = ANY(%s) "
        "GROUP BY block_verdict, block_flags ORDER BY n DESC LIMIT 30",
        (ACTIVE_INSTRUMENTS,),
    )
    scatter = query(
        "SELECT zone_id, instrument, direction, ec_score, mfe_r, mae_r, r_result "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND mfe_r IS NOT NULL AND instrument = ANY(%s) "
        "ORDER BY exit_time DESC LIMIT 300",
        (ACTIVE_INSTRUMENTS,),
    )
    return {"ec": ec, "r1": r1, "conviction": conviction, "gate": gate, "scatter": scatter}


def api_zone_trades():
    overall = query(
        "SELECT COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS resolved, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, AVG(r_result) AS avg_r "
        "FROM zone_outcome WHERE instrument = ANY(%s)",
        (ACTIVE_INSTRUMENTS,),
    )
    by_r1 = query(
        "SELECT CASE WHEN zone_confluence < 6 THEN '0 <6' WHEN zone_confluence < 7 THEN '1 6-7' "
        "WHEN zone_confluence < 8 THEN '2 7-8' WHEN zone_confluence < 9 THEN '3 8-9' ELSE '4 9+' END AS bucket, "
        "COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM zone_outcome WHERE r_result IS NOT NULL AND instrument = ANY(%s) GROUP BY 1 ORDER BY 1",
        (ACTIVE_INSTRUMENTS,),
    )
    by_instrument = query(
        "SELECT instrument, COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS n, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, AVG(r_result) AS avg_r "
        "FROM zone_outcome WHERE instrument = ANY(%s) GROUP BY instrument ORDER BY total_r DESC",
        (ACTIVE_INSTRUMENTS,),
    )
    scatter = query(
        "SELECT zone_id, instrument, direction, mfe_r, mae_r, r_result "
        "FROM zone_outcome WHERE r_result IS NOT NULL AND mfe_r IS NOT NULL AND instrument = ANY(%s) "
        "ORDER BY exit_time DESC NULLS LAST, resolved_utc DESC LIMIT 300",
        (ACTIVE_INSTRUMENTS,),
    )
    recent = query(
        "SELECT zone_id, instrument, week, label, direction, status, entry, sl_dist, "
        "r_result, mfe_r, mae_r, fill_time, exit_time "
        "FROM zone_outcome WHERE instrument = ANY(%s) ORDER BY resolved_utc DESC LIMIT 100",
        (ACTIVE_INSTRUMENTS,),
    )
    return {"overall": overall[0] if overall else {}, "by_r1": by_r1, "by_instrument": by_instrument, "scatter": scatter, "recent": recent}


def api_zone_trades_atr():
    overall = query(
        "SELECT COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS resolved, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, AVG(r_result) AS avg_r "
        "FROM zone_atr_sl_outcome WHERE instrument = ANY(%s)",
        (ACTIVE_INSTRUMENTS,),
    )
    by_r1 = query(
        "SELECT CASE WHEN zone_confluence < 6 THEN '0 <6' WHEN zone_confluence < 7 THEN '1 6-7' "
        "WHEN zone_confluence < 8 THEN '2 7-8' WHEN zone_confluence < 9 THEN '3 8-9' ELSE '4 9+' END AS bucket, "
        "COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM zone_atr_sl_outcome WHERE r_result IS NOT NULL AND instrument = ANY(%s) GROUP BY 1 ORDER BY 1",
        (ACTIVE_INSTRUMENTS,),
    )
    by_instrument = query(
        "SELECT instrument, COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS n, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, AVG(r_result) AS avg_r "
        "FROM zone_atr_sl_outcome WHERE instrument = ANY(%s) GROUP BY instrument ORDER BY total_r DESC",
        (ACTIVE_INSTRUMENTS,),
    )
    scatter = query(
        "SELECT zone_id, instrument, direction, mfe_r, mae_r, r_result "
        "FROM zone_atr_sl_outcome WHERE r_result IS NOT NULL AND mfe_r IS NOT NULL AND instrument = ANY(%s) "
        "ORDER BY exit_time DESC NULLS LAST, resolved_utc DESC LIMIT 300",
        (ACTIVE_INSTRUMENTS,),
    )
    recent = query(
        "SELECT zone_id, instrument, week, label, direction, status, entry, sl_dist, "
        "r_result, mfe_r, mae_r, fill_time, exit_time "
        "FROM zone_atr_sl_outcome WHERE instrument = ANY(%s) ORDER BY resolved_utc DESC LIMIT 100",
        (ACTIVE_INSTRUMENTS,),
    )
    return {"overall": overall[0] if overall else {}, "by_r1": by_r1, "by_instrument": by_instrument, "scatter": scatter, "recent": recent}


def api_macro():
    return {
        "yield_env": (query("SELECT title, body, updated_utc FROM context_doc WHERE doc_key = 'yield_environment'") or [None])[0],
        "macro_series": query(
            "SELECT series_id, date, value FROM macro_series "
            "WHERE date >= (now() AT TIME ZONE 'utc')::date - 400 ORDER BY series_id, date"
        ),
        "market_series": query(
            "SELECT source, symbol, date, value FROM market_series "
            "WHERE date >= (now() AT TIME ZONE 'utc')::date - 400 ORDER BY symbol, date"
        ),
        "cot": query(
            "SELECT contract, date, long, short, net, net_prev FROM cot "
            "WHERE date >= (now() AT TIME ZONE 'utc')::date - 400 ORDER BY contract, date"
        ),
        "gld": query(
            "SELECT date, tonnes, aum_usd, spot FROM gld_holdings "
            "WHERE date >= (now() AT TIME ZONE 'utc')::date - 400 ORDER BY date"
        ),
    }


def api_news(instrument: str = ""):
    if instrument:
        return query(
            "SELECT datetime_utc, category, headline, source, url, summary, related "
            "FROM news WHERE related ILIKE %s OR headline ILIKE %s "
            "ORDER BY datetime_utc DESC LIMIT 60",
            (f"%{instrument}%", f"%{instrument}%"),
        )
    return query(
        "SELECT datetime_utc, category, headline, source, url, summary, related "
        "FROM news ORDER BY datetime_utc DESC LIMIT 60"
    )


def api_config():
    return {
        "cb_calendar": query(
            "SELECT bank_code, name, time_note, hard_block, caution, dates, verified_through, updated_utc "
            "FROM cb_calendar ORDER BY bank_code"
        ),
        "intervention_watch": query(
            "SELECT pair, intervention_level, caution_band, regime, verified_through, updated_utc "
            "FROM intervention_watch ORDER BY pair"
        ),
        "jawboning": query(
            "SELECT pair, event_date, official, quote, source, created_utc "
            "FROM intervention_jawboning ORDER BY event_date DESC LIMIT 40"
        ),
    }


DOC_TABLE = {
    "rulebook": "rulebook",
    "context": "context_doc",
    "forecast": "forecast_doc",
    "validation": "validation_doc",
}


def api_doc_history(doc_type: str, key: str):
    table = DOC_TABLE.get(doc_type)
    source_table = {"context": "context_doc"}.get(doc_type, table)
    return query(
        "SELECT source_table, doc_key, version, saved_utc FROM doc_history "
        "WHERE source_table = %s AND doc_key = %s ORDER BY version DESC",
        (source_table, key),
    )


def api_zones():
    return query(
        """
        SELECT z.zone_id, z.instrument, z.week, z.label, z.direction,
               z.zone_bottom, z.zone_top, z.zone_confluence, z.conviction,
               o.status, o.entry, o.sl_dist, o.r_result,
               o.fill_time, o.mfe_r, o.mae_r
        FROM zone_ledger z
        JOIN zone_outcome o ON o.zone_id = z.zone_id
        WHERE o.status IN ('PENDING', 'RUNNING') AND z.instrument = ANY(%s)
        ORDER BY z.instrument, z.week DESC, z.label
        """,
        (ACTIVE_INSTRUMENTS,),
    )


def api_zones_atr():
    return query(
        """
        SELECT z.zone_id, z.instrument, z.week, z.label, z.direction,
               z.zone_bottom, z.zone_top, z.zone_confluence, z.conviction,
               o.status AS atr_status, o.entry, o.sl_dist, o.r_result,
               o.fill_time, o.mfe_r, o.mae_r
        FROM zone_ledger z
        JOIN zone_atr_sl_outcome o ON o.zone_id = z.zone_id
        WHERE o.status IN ('PENDING', 'RUNNING') AND z.instrument = ANY(%s)
        ORDER BY z.instrument, z.week DESC, z.label
        """,
        (ACTIVE_INSTRUMENTS,),
    )


def api_pnl():
    overall = query(
        "SELECT COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS resolved, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, "
        "AVG(r_result) AS avg_r "
        "FROM trade_outcome WHERE instrument = ANY(%s)",
        (ACTIVE_INSTRUMENTS,),
    )
    by_instrument = query(
        "SELECT instrument, COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS n, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, AVG(r_result) AS avg_r "
        "FROM trade_outcome WHERE instrument = ANY(%s) GROUP BY instrument ORDER BY total_r DESC",
        (ACTIVE_INSTRUMENTS,),
    )
    recent = query(
        "SELECT zone_id, instrument, week, direction, status, ec_score, "
        "entry, r_result, mfe_r, mae_r, fill_time, exit_time, block_flags "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND instrument = ANY(%s) "
        "ORDER BY exit_time DESC NULLS LAST, resolved_utc DESC LIMIT 50",
        (ACTIVE_INSTRUMENTS,),
    )
    return {"overall": overall[0] if overall else {}, "by_instrument": by_instrument, "recent": recent}


def api_validations():
    return query(
        "SELECT zone_id, instrument, validation_date, verdict, entry_confluence, "
        "limit_price, hard_block_flags, reason, updated_utc "
        "FROM validation_verdict WHERE instrument = ANY(%s) "
        "ORDER BY validation_date DESC, updated_utc DESC LIMIT 60",
        (ACTIVE_INSTRUMENTS,),
    )


def api_pipeline():
    return query(
        "SELECT run_id, job_name, instrument, status, started_utc, finished_utc, "
        "duration_s, returncode, "
        "COALESCE(NULLIF(error, ''), NULLIF(stderr_tail, ''), NULLIF(stdout_tail, ''), '') AS error, "
        "stdout_tail, stderr_tail "
        "FROM pipeline_run WHERE instrument IS NULL OR instrument = ANY(%s) "
        "ORDER BY started_utc DESC LIMIT 40",
        (ACTIVE_INSTRUMENTS,),
    )


def api_calibration():
    return {
        "zone_outcome": query(
            "SELECT instrument, direction, status, COUNT(*) AS n, AVG(r_result) AS avg_r "
            "FROM zone_outcome WHERE instrument = ANY(%s) GROUP BY instrument, direction, status "
            "ORDER BY instrument, direction, status",
            (ACTIVE_INSTRUMENTS,),
        ),
        "trade_outcome": query(
            "SELECT instrument, direction, status, COUNT(*) AS n, AVG(r_result) AS avg_r "
            "FROM trade_outcome WHERE instrument = ANY(%s) GROUP BY instrument, direction, status "
            "ORDER BY instrument, direction, status",
            (ACTIVE_INSTRUMENTS,),
        ),
    }


def api_docs():
    return query(
        """
        SELECT 'rulebook' AS doc_type, doc_key, kind, instrument, NULL::text AS week,
               title, version, updated_utc FROM rulebook WHERE instrument IS NULL OR instrument = ANY(%s)
        UNION ALL
        SELECT 'context', doc_key, kind, NULL, NULL, title, version, updated_utc FROM context_doc
        UNION ALL
        SELECT 'forecast', doc_key, 'forecast', instrument, week, title, version, updated_utc FROM forecast_doc WHERE instrument = ANY(%s)
        UNION ALL
        SELECT 'validation', doc_key, 'validation', instrument, week, title, version, updated_utc FROM validation_doc WHERE instrument = ANY(%s)
        ORDER BY doc_type, doc_key
        """,
        (ACTIVE_INSTRUMENTS, ACTIVE_INSTRUMENTS, ACTIVE_INSTRUMENTS),
    )


def api_doc(doc_type: str, key: str):
    table = DOC_TABLE.get(doc_type)
    if not table:
        raise ValueError(f"unknown doc_type: {doc_type}")
    rows = query(f"SELECT * FROM {table} WHERE doc_key = %s", (key,))
    return rows[0] if rows else None


API = {
    "/api/health": api_health,
    "/api/zones": api_zones,
    "/api/zones_atr": api_zones_atr,
    "/api/pnl": api_pnl,
    "/api/validations": api_validations,
    "/api/pipeline": api_pipeline,
    "/api/calibration": api_calibration,
    "/api/docs": api_docs,
    "/api/trades": api_trades,
    "/api/notifications": api_notifications,
    "/api/gates": api_gates,
    "/api/symbols": api_symbols,
    "/api/quarantine": api_quarantine,
    "/api/equity": api_equity,
    "/api/buckets": api_buckets,
    "/api/zone_trades": api_zone_trades,
    "/api/zone_trades_atr": api_zone_trades_atr,
    "/api/macro": api_macro,
    "/api/config": api_config,
}

app = FastAPI(title="swing-agent dashboard", docs_url="/api/docs-ui")


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})


@app.get("/health")
def health():
    return {"ok": True, "time": utc_now()}


def _register_simple_routes():
    # Closures over `fn` need a default-arg capture — a bare loop var would bind
    # late and every route would call the last `fn` in API.
    for path, fn in API.items():
        def make_handler(fn=fn):
            def handler():
                return {"ok": True, "data": fn()}
            return handler
        app.get(path)(make_handler())


_register_simple_routes()


@app.get("/api/ohlc")
def ohlc_route(symbol: str, tf: str = "1day"):
    return {"ok": True, "data": api_ohlc(symbol, tf)}


@app.get("/api/news")
def news_route(instrument: str = ""):
    return {"ok": True, "data": api_news(instrument)}


@app.get("/api/doc-history")
def doc_history_route(type: str, key: str):
    return {"ok": True, "data": api_doc_history(type, key)}


@app.get("/api/doc")
def doc_route(type: str, key: str):
    try:
        return {"ok": True, "data": api_doc(type, key)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/{full_path:path}")
def serve_static(full_path: str):
    rel = full_path.lstrip("/") or "index.html"
    target = (DIST_DIR / rel).resolve()
    if not str(target).startswith(str(DIST_DIR.resolve())) or not target.is_file():
        target = DIST_DIR / "index.html"
    if not target.is_file():
        raise HTTPException(status_code=404, detail="dashboard bundle not built")
    return FileResponse(target)


def main() -> int:
    # NOTE: this service builds from its own isolated Docker context (./src/dashboard,
    # see Dockerfile) and cannot reach src/logging_config.py at the repo root — plain
    # print-logging by design, matching server.py.
    import uvicorn

    print(f"swing-agent dashboard starting on {HOST}:{PORT} (dist={DIST_DIR})", flush=True)
    uvicorn.run(app, host=HOST, port=PORT)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
