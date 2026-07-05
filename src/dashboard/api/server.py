#!/usr/bin/env python3
"""
server.py — read-only monitoring dashboard for swing-agent.

Standalone by design: it does NOT import the mcp-server `tools.py` (that pulls the
heavy `engine` package). It carries its own tiny `pg_connect` + `query` and a fixed
map of read-only SQL behind `/api/*`. Also serves the built Vite bundle (static
files) so the browser fetches same-origin `/api/*` — no CORS, no token in the page.

Bind 127.0.0.1 (compose default) and view over an SSH tunnel.
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import traceback
from datetime import date, datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.getenv("DASHBOARD_PORT", "8888"))
# Where the built Vite bundle lives. Defaults to ../static relative to this file
# (populated by the Docker build stage). Override with DASHBOARD_DIST.
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
# API endpoints — each returns a JSON-serialisable object. Read-only SQL only.
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
            "SELECT 'ohlc' AS source, MAX(datetime) AS latest FROM ohlc "
            "UNION ALL SELECT 'news', MAX(datetime_utc) FROM news "
            "UNION ALL SELECT 'econ_calendar', MAX(date)::timestamptz FROM econ_calendar"
        ),
        # Per-instrument OHLC freshness — a single stale pair hides behind the global MAX.
        "ohlc_freshness": query(
            "SELECT symbol, tf, MAX(datetime) AS latest, COUNT(*) AS bars "
            "FROM ohlc GROUP BY symbol, tf ORDER BY symbol, tf"
        ),
        "server_time": utc_now(),
    }


def api_trades():
    # Live order book (real trade_log, distinct from the replay in trade_outcome).
    return query(
        "SELECT zone_id, instrument, week, label, direction, status, entry_confluence, "
        "limit_price, sl_price, tp_price, entry_price, fill_time, exit_price, exit_time, "
        "r_result, hard_block_flags, reason, validation_date, updated_utc "
        "FROM trade_log ORDER BY "
        "CASE status WHEN 'FILLED' THEN 0 WHEN 'PENDING' THEN 1 ELSE 2 END, "
        "updated_utc DESC LIMIT 100"
    )


def api_notifications():
    counts = query(
        "SELECT status, COUNT(*) AS n FROM notification_event GROUP BY status ORDER BY status"
    )
    recent = query(
        "SELECT event_id, event_type, instrument, zone_id, title, message, status, "
        "created_utc, sent_utc, error FROM notification_event "
        "ORDER BY created_utc DESC LIMIT 40"
    )
    return {"counts": counts, "recent": recent}


def api_gates():
    return {
        # Upcoming CB decisions — current week + next week only (Mon this week → Sun next week).
        "cb": query(
            "SELECT bank_code, name, hard_block, caution, time_note, "
            "(d->>'date')::date AS decision_date, d->>'status' AS decision_status "
            "FROM cb_calendar, jsonb_array_elements(dates) AS d "
            "WHERE (d->>'date')::date >= date_trunc('week', now() AT TIME ZONE 'utc')::date "
            "AND (d->>'date')::date < date_trunc('week', now() AT TIME ZONE 'utc')::date + 14 "
            "ORDER BY decision_date LIMIT 30"
        ),
        # High-impact econ, current week + next week only (Mon this week → Sun next week).
        "econ": query(
            "SELECT date, time_utc, country, event, impact, estimate, actual, prev "
            "FROM econ_calendar "
            "WHERE date >= date_trunc('week', now() AT TIME ZONE 'utc')::date "
            "AND date < date_trunc('week', now() AT TIME ZONE 'utc')::date + 14 "
            "AND upper(coalesce(impact,'')) IN ('HIGH','MEDIUM') "
            "ORDER BY date, time_utc LIMIT 60"
        ),
        # JPY intervention watch — spot-vs-level gate.
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
    rows.reverse()  # chronological for the candlestick
    # Zones for this instrument to overlay (band + limit/invalidation/tp lines).
    zones = query(
        "SELECT zone_id, week, label, direction, zone_bottom, zone_top, status, "
        "limit_price, invalidation_level, tp_anchor, published_utc "
        "FROM zone_ledger WHERE instrument = %s ORDER BY published_utc DESC LIMIT 12",
        (symbol,),
    )
    return {"symbol": symbol, "tf": tf, "bars": rows, "zones": zones}


def api_symbols():
    return query("SELECT DISTINCT symbol, tf FROM ohlc ORDER BY symbol, tf")


def api_quarantine():
    return query(
        "SELECT symbol, tf, datetime, action, open, high, low, close, ref_close, flagged_utc "
        "FROM ohlc_quarantine ORDER BY flagged_utc DESC NULLS LAST, datetime DESC LIMIT 100"
    )


def api_equity():
    # Cumulative R over time — the running equity curve.
    return query(
        "SELECT zone_id, instrument, direction, exit_time, r_result, "
        "SUM(r_result) OVER (ORDER BY exit_time, resolved_utc) AS cum_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND exit_time IS NOT NULL "
        "ORDER BY exit_time, resolved_utc"
    )


def api_buckets():
    ec = query(
        "SELECT CASE WHEN ec_score < 5 THEN '0 <5' WHEN ec_score < 6 THEN '1 5-6' "
        "WHEN ec_score < 7 THEN '2 6-7' WHEN ec_score < 8 THEN '3 7-8' ELSE '4 8+' END AS bucket, "
        "COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL GROUP BY 1 ORDER BY 1"
    )
    r1 = query(
        "SELECT CASE WHEN zone_confluence < 6 THEN '0 <6' WHEN zone_confluence < 7 THEN '1 6-7' "
        "WHEN zone_confluence < 8 THEN '2 7-8' WHEN zone_confluence < 9 THEN '3 8-9' ELSE '4 9+' END AS bucket, "
        "COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL GROUP BY 1 ORDER BY 1"
    )
    conviction = query(
        "SELECT conviction, COUNT(*) AS n, COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "AVG(r_result) AS avg_r, SUM(r_result) AS total_r "
        "FROM trade_outcome WHERE r_result IS NOT NULL GROUP BY conviction ORDER BY conviction"
    )
    # Gate-accuracy audit — was blocking correct? block_verdict summarises it.
    gate = query(
        "SELECT block_verdict, block_flags, COUNT(*) AS n, AVG(r_result) AS avg_r "
        "FROM trade_outcome WHERE block_verdict IS NOT NULL "
        "GROUP BY block_verdict, block_flags ORDER BY n DESC LIMIT 30"
    )
    # MFE/MAE scatter — are wins capped early, losses run?
    scatter = query(
        "SELECT zone_id, instrument, direction, ec_score, mfe_r, mae_r, r_result "
        "FROM trade_outcome WHERE r_result IS NOT NULL AND mfe_r IS NOT NULL "
        "ORDER BY exit_time DESC LIMIT 300"
    )
    return {"ec": ec, "r1": r1, "conviction": conviction, "gate": gate, "scatter": scatter}


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


def api_doc_history(doc_type: str, key: str):
    table = DOC_TABLE.get(doc_type)
    source_table = {"context": "context_doc"}.get(doc_type, table)
    return query(
        "SELECT source_table, doc_key, version, saved_utc FROM doc_history "
        "WHERE source_table = %s AND doc_key = %s ORDER BY version DESC",
        (source_table, key),
    )


def api_zones():
    # Open zones + the most recent validation verdict per zone.
    return query(
        """
        SELECT z.zone_id, z.instrument, z.week, z.label, z.direction,
               z.zone_bottom, z.zone_top, z.zone_confluence, z.conviction,
               z.status, z.daily_verdict, z.entry_confluence, z.limit_price,
               z.invalidation_level, z.tp_anchor, z.validated_date, z.published_utc,
               v.verdict AS latest_verdict, v.validation_date AS latest_verdict_date,
               v.hard_block_flags
        FROM zone_ledger z
        LEFT JOIN LATERAL (
            SELECT verdict, validation_date, hard_block_flags
            FROM validation_verdict vv
            WHERE vv.zone_id = z.zone_id
            ORDER BY validation_date DESC, updated_utc DESC
            LIMIT 1
        ) v ON true
        WHERE z.status = 'OPEN'
        ORDER BY z.instrument, z.week DESC, z.label
        """
    )


def api_zones_atr():
    # Comparison view: same zones, but "open" per the ATR-SL replay (zone_atr_sl_outcome),
    # which does not drive zone_ledger.status — a zone can differ here vs /api/zones.
    return query(
        """
        SELECT z.zone_id, z.instrument, z.week, z.label, z.direction,
               z.zone_bottom, z.zone_top, z.zone_confluence, z.conviction,
               o.status AS atr_status, o.entry, o.sl_dist, o.r_result,
               o.fill_time, o.mfe_r, o.mae_r
        FROM zone_ledger z
        JOIN zone_atr_sl_outcome o ON o.zone_id = z.zone_id
        WHERE o.status IN ('PENDING', 'RUNNING')
        ORDER BY z.instrument, z.week DESC, z.label
        """
    )


def api_pnl():
    overall = query(
        "SELECT COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS resolved, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, "
        "AVG(r_result) AS avg_r "
        "FROM trade_outcome"
    )
    by_instrument = query(
        "SELECT instrument, COUNT(*) FILTER (WHERE r_result IS NOT NULL) AS n, "
        "COUNT(*) FILTER (WHERE r_result > 0) AS wins, "
        "COALESCE(SUM(r_result), 0) AS total_r, AVG(r_result) AS avg_r "
        "FROM trade_outcome GROUP BY instrument ORDER BY total_r DESC"
    )
    recent = query(
        "SELECT zone_id, instrument, week, direction, status, ec_score, "
        "entry, r_result, mfe_r, mae_r, fill_time, exit_time, block_flags "
        "FROM trade_outcome WHERE r_result IS NOT NULL "
        "ORDER BY exit_time DESC NULLS LAST, resolved_utc DESC LIMIT 50"
    )
    return {"overall": overall[0] if overall else {}, "by_instrument": by_instrument, "recent": recent}


def api_validations():
    return query(
        "SELECT zone_id, instrument, validation_date, verdict, entry_confluence, "
        "limit_price, hard_block_flags, reason, updated_utc "
        "FROM validation_verdict ORDER BY validation_date DESC, updated_utc DESC LIMIT 60"
    )


def api_pipeline():
    return query(
        "SELECT run_id, job_name, instrument, status, started_utc, finished_utc, "
        "duration_s, returncode, error, stderr_tail "
        "FROM pipeline_run ORDER BY started_utc DESC LIMIT 40"
    )


def api_calibration():
    return {
        "zone_outcome": query(
            "SELECT instrument, direction, status, COUNT(*) AS n, AVG(r_result) AS avg_r "
            "FROM zone_outcome GROUP BY instrument, direction, status "
            "ORDER BY instrument, direction, status"
        ),
        "trade_outcome": query(
            "SELECT instrument, direction, status, COUNT(*) AS n, AVG(r_result) AS avg_r "
            "FROM trade_outcome GROUP BY instrument, direction, status "
            "ORDER BY instrument, direction, status"
        ),
    }


def api_docs():
    # Unified metadata (no body) across the four prose tables (Phase 1).
    return query(
        """
        SELECT 'rulebook' AS doc_type, doc_key, kind, instrument, NULL::text AS week,
               title, version, updated_utc FROM rulebook
        UNION ALL
        SELECT 'context', doc_key, kind, NULL, NULL, title, version, updated_utc FROM context_doc
        UNION ALL
        SELECT 'forecast', doc_key, 'forecast', instrument, week, title, version, updated_utc FROM forecast_doc
        UNION ALL
        SELECT 'validation', doc_key, 'validation', instrument, week, title, version, updated_utc FROM validation_doc
        ORDER BY doc_type, doc_key
        """
    )


DOC_TABLE = {
    "rulebook": "rulebook",
    "context": "context_doc",
    "forecast": "forecast_doc",
    "validation": "validation_doc",
}


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
    # Tab: Dashboard
    "/api/trades": api_trades,
    "/api/notifications": api_notifications,
    "/api/gates": api_gates,
    # Tab: Charts
    "/api/symbols": api_symbols,
    "/api/quarantine": api_quarantine,
    # Tab: Performance
    "/api/equity": api_equity,
    "/api/buckets": api_buckets,
    # Tab: Macro
    "/api/macro": api_macro,
    "/api/config": api_config,
}

# Endpoints that take query params — dispatched in do_GET (parse then call).
def _q(qs: dict, name: str, default: str = "") -> str:
    return (qs.get(name) or [default])[0]


QUERY_API = {
    "/api/ohlc": lambda qs: api_ohlc(_q(qs, "symbol"), _q(qs, "tf", "1day")),
    "/api/news": lambda qs: api_news(_q(qs, "instrument")),
    "/api/doc-history": lambda qs: api_doc_history(_q(qs, "type"), _q(qs, "key")),
}


class Handler(BaseHTTPRequestHandler):
    server_version = "swing-agent-dashboard/0.1"

    def log_message(self, fmt, *args):
        print(f"{utc_now()} {self.client_address[0]} {fmt % args}", flush=True)

    def _json(self, status: int, payload):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: str):
        # Map URL path to a file under DIST_DIR; SPA fallback to index.html.
        rel = path.lstrip("/") or "index.html"
        target = (DIST_DIR / rel).resolve()
        if not str(target).startswith(str(DIST_DIR.resolve())) or not target.is_file():
            target = DIST_DIR / "index.html"
        if not target.is_file():
            return self._json(HTTPStatus.NOT_FOUND, {"error": "dashboard bundle not built"})
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/health":
            return self._json(HTTPStatus.OK, {"ok": True, "time": utc_now()})
        if path == "/api/doc":
            qs = parse_qs(parsed.query)
            try:
                data = api_doc((qs.get("type") or [""])[0], (qs.get("key") or [""])[0])
                return self._json(HTTPStatus.OK, {"ok": True, "data": data})
            except Exception as exc:
                return self._json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": str(exc), "trace": traceback.format_exc(limit=3)},
                )
        if path in QUERY_API:
            qs = parse_qs(parsed.query)
            try:
                return self._json(HTTPStatus.OK, {"ok": True, "data": QUERY_API[path](qs)})
            except Exception as exc:
                return self._json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": str(exc), "trace": traceback.format_exc(limit=3)},
                )
        if path in API:
            try:
                return self._json(HTTPStatus.OK, {"ok": True, "data": API[path]()})
            except Exception as exc:
                return self._json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": str(exc), "trace": traceback.format_exc(limit=3)},
                )
        return self._serve_static(path)


def main() -> int:
    print(f"swing-agent dashboard starting on {HOST}:{PORT} (dist={DIST_DIR})", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
