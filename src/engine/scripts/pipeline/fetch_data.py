"""
Multi-instrument data pipeline — fetch every source and sync it to the canonical DB.

Usage:
    bash scripts/pyrun.sh scripts/pipeline/fetch_data.py                        # xauusd
    bash scripts/pyrun.sh scripts/pipeline/fetch_data.py --force                # xauusd, re-fetch full
    bash scripts/pyrun.sh scripts/pipeline/fetch_data.py --instrument all       # every registered pair

Each run (scheduler calls it every 15/30min per instrument):
    TD 15M fetch (1 API call) → resample → 1h/4h/1day → upsert `ohlc`
    FRED / DXY / commodities  → `macro_series` / `market_series`
    COT (CFTC) → `cot`   ·   ETF flows → `gld_holdings`   ·   news → `news`   ·   econ → `econ_calendar`

All output is DB-canonical; the AI leg reads it back through the MCP tools
(get_zone_context / sql_query / get_news / get_econ). No snapshot file is written —
the old weekly_pull_*.txt dump was retired once get_zone_context recomputed its
content live from the DB.

Requirements: pip install requests pandas yfinance python-dotenv
"""

import os, sys, argparse, time, importlib
import requests, pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

# ── INSTRUMENT REGISTRY ───────────────────────────────────────────────────────

REGISTERED_INSTRUMENTS = {
    "xauusd": "config.xauusd",
    "eurusd": "config.eurusd",
    "gbpusd": "config.gbpusd",
    "eurgbp": "config.eurgbp",   # cross — EG1 (data); macro placeholder, see D022
    "audusd": "config.audusd",   # D024 pair #1 — USD-quote major, no daily RBA series
    "nzdusd": "config.nzdusd",   # D024 pair #2 — USD-quote major, no daily RBNZ series
    "usdcad": "config.usdcad",   # D024 pair #3 — USD-BASE (inverted), oil leg, COT inverted
    "usdchf": "config.usdchf",   # D024 pair #4 — USD-BASE, safe-haven CHF, SNB regime, COT inverted
    "usdjpy": "config.usdjpy",   # D024 pair #5 — USD-BASE, first JPY pair (pip 0.01, TICK 650, 3dp)
    "eurjpy": "config.eurjpy",   # D024 pair #6 — first cross-JPY (USD_BETA_SIGN=0, JPY pip, one-leg macro)
    "gbpjpy": "config.gbpjpy",   # D024 pair #7 — cross-JPY #2 (one-leg macro = SONIA, COT off, high ATR)
}

_instrument_cfg = None  # set by load_instrument()


def load_instrument(name: str):
    """Load instrument config and rebind module globals. Must be called before fetch/compute."""
    global _instrument_cfg, SYMBOL, SYM_CLEAN, TD_DIR, FRED_SERIES, GLD_HOLD_CSV, TICK_MULTIPLIER, PRICE_DP

    if name not in REGISTERED_INSTRUMENTS:
        raise ValueError(f"Unknown instrument '{name}'. Registered: {list(REGISTERED_INSTRUMENTS)}")

    # Add project root to sys.path so instruments/ package is importable
    _root = str(Path(__file__).resolve().parents[2])
    if _root not in sys.path:
        sys.path.insert(0, _root)

    cfg = importlib.import_module(REGISTERED_INSTRUMENTS[name])
    _instrument_cfg = cfg

    SYMBOL      = cfg.SYMBOL
    SYM_CLEAN   = cfg.SYM_CLEAN
    TD_DIR      = Path(cfg.TD_DIR)
    FRED_SERIES = cfg.FRED_SERIES
    # TICK_MULTIPLIER: legacy price-scale constant per instrument, retained only as a
    # heuristic input to PRICE_DP (display precision) below — no longer used for lot sizing.
    TICK_MULTIPLIER = getattr(cfg, "TICK_MULTIPLIER", 100)
    # Price display/rounding precision (shared helper — same rule zone_context uses):
    # $-scale gold (TICK<=100) → 2dp; pip-scale FX → 5dp; JPY pairs set PRICE_DP=3 in config.
    import config as _config_pkg
    PRICE_DP = _config_pkg.price_dp(cfg)
    if cfg.ETF_ENABLED and cfg.ETF_HOLDINGS_CSV:
        GLD_HOLD_CSV = Path(cfg.ETF_HOLDINGS_CSV)

    print(f"[instrument] {cfg.DISPLAY_NAME} loaded")


_SCRIPTS_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(_SCRIPTS_ROOT, "lib"))
sys.path.insert(0, _SCRIPTS_ROOT)  # for `db` import below (canonical store — not a fallback)
from ohlc_store import upsert, last_dt as manifest_last_dt

try:                       # canonical store
    import db
except Exception:
    db = None

RUN_ISSUES = []
_ISSUE_SEEN = set()
_SHARED_CACHE = {}


def _record_issue(kind, detail):
    issue = f"{kind}: {detail}"
    if issue in _ISSUE_SEEN:
        return
    _ISSUE_SEEN.add(issue)
    RUN_ISSUES.append(issue)


def _db_sync(label, fn):
    """Best-effort sync into the canonical DB. Never breaks fetch; caller reports health."""
    if db is None:
        _record_issue("db", f"{label} skipped; db module unavailable")
        return
    try:
        fn()
    except Exception as e:
        _record_issue("db", f"{label} failed: {e}")
        print(f"  ⚠ DB sync {label} failed: {e}")


def _date_iso(value):
    if value is None or value == "":
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return str(value)[:10]
    return ts.strftime("%Y-%m-%d")


def _is_critical_issue(issue):
    return issue.startswith(("fetch:", "db:", "fred:", "dxy:", "commodity:"))


def _print_health(start_issue_count):
    new_issues = RUN_ISSUES[start_issue_count:]
    if not new_issues:
        print("✅ data ready (DB canonical).")
        return
    critical = [i for i in new_issues if _is_critical_issue(i)]
    print(f"⚠ data ready with {len(new_issues)} issue(s), critical={len(critical)}.")
    for issue in new_issues[:12]:
        print(f"  - {issue}")
    if len(new_issues) > 12:
        print(f"  - ... {len(new_issues) - 12} more")


def _shared_result(name, force, fn):
    key = (name, bool(force))
    if key not in _SHARED_CACHE:
        _SHARED_CACHE[key] = fn()
    return _SHARED_CACHE[key]


load_dotenv()

TWELVE_KEY = os.getenv("TWELVE_DATA_KEY")
FRED_KEY   = os.getenv("FRED_KEY")

# Defaults — overridden by load_instrument(); match xauusd so a no-arg run works.
SYMBOL    = "XAU/USD"
SYM_CLEAN = "xauusd"
TD_DIR    = Path("data/twelvedata/xauusd")
FRED_DIR  = Path("data/fred")
TICK_MULTIPLIER = 100   # price-scale constant (gold), used only to derive PRICE_DP display precision. Overridden by load_instrument.
PRICE_DP = 2            # price rounding precision (gold $-scale). FX→5. Overridden by load_instrument.

FRED_SERIES = ["DFII10", "DGS10", "T5YIE", "DFF", "VIXCLS"]
# DXY: ICE 6-currency index via yfinance DX-Y.NYB (not FRED DTWEXBGS which is 26-currency)
DXY_CSV       = Path("data/yahoo/DXY.csv")
GLD_HOLD_CSV  = Path("data/gld_holdings.csv")
COT_CACHE_DIR = Path("data/cftc")
ECON_DIR      = Path("data/econ_calendar")        # economic calendar (#1/#2, Forex Factory free JSON)
ECON_CSV      = ECON_DIR / "calendar.csv"
ECON_COLS     = ["date", "time_utc", "country", "event", "impact", "estimate", "actual", "prev", "unit"]
COMMODITIES_DIR = Path("data/commodities")        # intermarket (#3, yfinance)
NEWS_DIR      = Path("data/news")                  # news store (free RSS feeds, D025)
NEWS_CSV      = NEWS_DIR / "headlines.csv"
NEWS_COLS     = ["datetime_utc", "category", "headline", "source", "url", "summary", "related"]
# Per-pair headline keywords for the pull's NEWS FEED filter (US/Fed terms appended globally).
_NEWS_KEYWORDS = {
    "xauusd": ["gold", "bullion", "xau", "safe haven", "real yield"],
    "eurusd": ["euro", "ecb", "eurozone", "lagarde"],
    "gbpusd": ["pound", "sterling", "boe", "bank of england", "gilt"],
    "eurgbp": ["euro", "pound", "ecb", "boe"],
    "audusd": ["aussie", "australian dollar", "rba", "iron ore", "china", "copper"],
    "nzdusd": ["kiwi", "new zealand dollar", "rbnz", "dairy", "china"],
    "usdcad": ["loonie", "canadian dollar", "boc", "bank of canada", "oil", "crude", "wti"],
    "usdchf": ["franc", "swiss", "snb"],
    "usdjpy": ["yen", "boj", "bank of japan", "mof", "intervention", "ueda"],
    "eurjpy": ["yen", "euro", "boj", "ecb", "intervention"],
    "gbpjpy": ["yen", "pound", "boj", "boe", "intervention"],
}
TF_RESAMPLE = {"1h": "1h", "4h": "4h", "1day": "1D"}

# ── STEP 1: FETCH 15M + RESAMPLE ─────────────────────────────────────────────

MAX_15M_OUTPUTSIZE = 5000  # TD per-call cap; ~52 calendar days of 15M bars


def fetch_15m(force=False):
    last = manifest_last_dt("twelvedata", SYMBOL, "15min")
    if last is not None and last.tzinfo is not None:
        last = last.tz_convert("UTC").tz_localize(None)  # TD returns naive UTC strings; compare naive-to-naive
    if force or last is None:
        outputsize = 800
    else:
        # Size the request from the actual gap since the last stored bar, so a multi-day
        # lapse (vacation, dead sandbox) is backfilled instead of leaving a silent hole
        # that corrupts every resampled H4/D1 bar and ATR downstream.
        gap_secs  = (datetime.now(timezone.utc) - last.tz_localize("UTC")).total_seconds()
        gap_bars  = int(gap_secs / 900) + 50  # +50 margin for weekend/overlap
        if gap_bars > MAX_15M_OUTPUTSIZE:
            raise ValueError(
                f"15M gap since {last} exceeds one API page ({gap_bars} bars > {MAX_15M_OUTPUTSIZE}). "
                f"Run: bash scripts/pyrun.sh scripts/backfill/backfill_twelvedata.py --tf 15min --forward-only"
            )
        outputsize = max(200, gap_bars)
    r = requests.get("https://api.twelvedata.com/time_series", params={
        "symbol": SYMBOL, "interval": "15min",
        "outputsize": outputsize, "timezone": "UTC", "apikey": TWELVE_KEY,
    }, timeout=20)
    data = r.json()
    if "code" in data:
        raise ValueError(f"TD 15min: {data.get('message', data)}")
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col])
    df["volume"] = pd.to_numeric(df.get("volume", 0))
    df = df.sort_values("datetime").reset_index(drop=True)
    if not force and last is not None:
        df = df[df["datetime"] > last]
    return df

def resample_all():
    src = db.read_ohlc(SYMBOL, "15min") if db else None   # DB master; CSV fallback for cold start
    if src is None or src.empty:
        src = pd.read_csv(TD_DIR / "15min.csv")
    src = src.copy()
    src["datetime"] = pd.to_datetime(src["datetime"])
    for c in ["open", "high", "low", "close", "volume"]:
        if c in src.columns:
            src[c] = pd.to_numeric(src[c], errors="coerce")
    src = src.sort_values("datetime").set_index("datetime")
    results = []
    for tf, rule in TF_RESAMPLE.items():
        agg = src.resample(rule, label="left", closed="left").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
        }).dropna(subset=["open", "close"]).reset_index()
        info = upsert("twelvedata", SYMBOL, tf, agg)
        results.append((tf, len(agg), info["last_dt"]))
    return results

# ── STEP 2: FRED UPDATE ───────────────────────────────────────────────────────

def update_fred(force=False, series=None):
    """Fetch/append FRED series into the `macro_series` table. `series` defaults to the
    instrument's FRED_SERIES; pass an explicit list (e.g. commodity ids) to reuse the path.
    Incremental bookmark = MAX(date) from the DB (no _manifest.json)."""
    series = series if series is not None else FRED_SERIES
    results  = []
    for sid in series:
        csv_path  = FRED_DIR / f"{sid}.csv"
        last_date = _date_iso(db.last_series_date("macro_series", {"series_id": sid}) if db else None)
        obs_start = ((datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
                     if (force or not last_date) else last_date)
        try:
            r   = requests.get("https://api.stlouisfed.org/fred/series/observations",
                               params={"series_id": sid, "observation_start": obs_start,
                                       "api_key": FRED_KEY, "file_type": "json"}, timeout=15)
            r.raise_for_status()
            payload = r.json()
            if "error_code" in payload:
                raise RuntimeError(payload.get("error_message") or payload["error_code"])
            obs = payload.get("observations", [])
            raw = pd.DataFrame(obs)
            if raw.empty:
                new = pd.DataFrame(columns=["date", "value"])
            elif {"date", "value"}.issubset(raw.columns):
                new = raw[["date", "value"]].copy()
            else:
                raise RuntimeError(f"unexpected FRED payload columns: {list(raw.columns)}")
            new["date"] = pd.to_datetime(new["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            new["value"] = pd.to_numeric(new["value"], errors="coerce")
            new = new.dropna(subset=["date", "value"])
            if not force and last_date:
                new = new[new["date"] > last_date]
            if not new.empty:
                prior = db.read_slice("macro_series", {"series_id": sid}, ["date", "value"]) if db else None
                if (prior is None or prior.empty) and csv_path.exists():
                    prior = pd.read_csv(csv_path)[["date", "value"]]
                if prior is not None and not prior.empty:
                    prior = prior.copy()
                    prior["date"] = pd.to_datetime(prior["date"], errors="coerce").dt.strftime("%Y-%m-%d")
                    combined = (pd.concat([prior, new], ignore_index=True)
                                .dropna(subset=["date"])
                                .drop_duplicates("date", keep="last")
                                .sort_values("date").reset_index(drop=True))
                else:
                    combined = new
                _db_sync(f"macro_series:{sid}", lambda c=combined, s=sid: db.sync_slice(
                    "macro_series", {"series_id": s},
                    c.assign(series_id=s)[["series_id", "date", "value"]],
                    index_cols=["series_id", "date"]))
            results.append((sid, len(new), _date_iso(db.last_series_date("macro_series", {"series_id": sid}) if db else "?")))
        except Exception as e:
            _record_issue("fred", f"{sid} failed: {e}")
            results.append((sid, f"ERROR: {e}", last_date or "?"))
    return results

# ── STEP 3: LOAD LOCAL DATA ───────────────────────────────────────────────────

def load_ohlc(path):
    # Read from the DB `ohlc` table (kept live by ohlc_store.upsert); CSV fallback on miss.
    p = Path(path)
    df = db.read_ohlc(p.parent.name, p.stem, source=p.parent.parent.name) if db else None
    if df is None or df.empty:
        df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["open", "high", "low", "close"])

# ── STEP 4: INDICATORS ────────────────────────────────────────────────────────

def _drop_open_bar(df, freq_hours: float) -> pd.DataFrame:
    """Drop last row if its candle period hasn't closed yet (bar still forming).

    Uses UTC now vs (last_bar_open + freq_hours). Safe during weekends: the last
    bar of a closed session is always a completed candle, so nothing is dropped.
    """
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    last_ts = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else pd.Timestamp(df.index[-1])
    if now < last_ts + pd.Timedelta(hours=freq_hours):
        return df.iloc[:-1]
    return df


# ── Oscillators / channels referenced by confluence_criteria (D025 — now COMPUTED,
#    previously eyeballed). All on CLOSED bars; computed for both D1 and H4. ──────

# Pivots/swings/fibs live in structure.py (shared with the MCP zone-context tool);
# these thin wrappers inject this run's PRICE_DP so the call sites stay unchanged.
# ── STEP 5: EXTERNAL FETCHES (no API key) ────────────────────────────────────

def fetch_cot():
    """CFTC Legacy report (non-commercial long/short). Source: cftc.gov yearly zip.
    Caches deahistfo{YEAR}.zip (combined Futures-Only, all markets) in data/cftc/.
    Returns latest two weekly reports for the instrument's COT contract.
    """
    import zipfile
    contract = (_instrument_cfg.COT_CONTRACT_NAME if _instrument_cfg
                else "GOLD - COMMODITY EXCHANGE INC.")
    try:
        COT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        year = datetime.now(timezone.utc).year
        zip_path = COT_CACHE_DIR / f"deahistfo{year}.zip"
        # refetch if older than 24h or missing
        stale = (not zip_path.exists() or
                 (time.time() - zip_path.stat().st_mtime) > 24*3600)
        if stale:
            r = requests.get(f"https://www.cftc.gov/files/dea/history/deahistfo{year}.zip",
                             timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            zip_path.write_bytes(r.content)
        z = zipfile.ZipFile(zip_path)
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        # Exact match: main contract only (excludes MICRO variants sharing same date rows)
        mask = df["Market and Exchange Names"].astype(str).str.strip() == contract
        g = df[mask].copy()
        g["date"] = pd.to_datetime(g["As of Date in Form YYYY-MM-DD"], errors="coerce")
        g = g.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        if g.empty:
            return {"error": f"no rows for contract '{contract}' in zip"}
        long_col  = "Noncommercial Positions-Long (All)"
        short_col = "Noncommercial Positions-Short (All)"
        latest = g.iloc[-1]; prev = g.iloc[-2] if len(g) >= 2 else None
        net_now  = int(latest[long_col]) - int(latest[short_col])
        net_prev = (int(prev[long_col]) - int(prev[short_col])) if prev is not None else None
        return {"date": latest["date"].strftime("%Y-%m-%d"),
                "long": int(latest[long_col]),
                "short": int(latest[short_col]),
                "net": net_now, "net_prev": net_prev,
                "net_chg": (net_now-net_prev) if net_prev is not None else None}
    except Exception as e:
        return {"error": str(e)}

def fetch_gld_flows():
    """GLD ETF holdings via yfinance totalAssets + spot gold → tonnes.
    Stores daily snapshot in data/gld_holdings.csv to compute wk/mo deltas.
    """
    try:
        t = yf.Ticker("GLD")
        total_assets = float(t.info.get("totalAssets") or 0)
        if total_assets <= 0:
            return {"error": "yfinance totalAssets unavailable"}
        # spot gold (use latest D1 close from our pull)
        d1 = load_ohlc(TD_DIR / "1day.csv").sort_index()   # DB-backed (CSV fallback)
        spot = float(d1["close"].iloc[-1])
        oz_per_tonne = 32150.7466
        tonnes = total_assets / (spot * oz_per_tonne)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Append to history CSV (idempotent — keep latest per date)
        GLD_HOLD_CSV.parent.mkdir(parents=True, exist_ok=True)
        hist = db.read_table("gld_holdings") if db else None
        if (hist is None or hist.empty):
            hist = pd.read_csv(GLD_HOLD_CSV) if GLD_HOLD_CSV.exists() \
                else pd.DataFrame(columns=["date", "tonnes", "aum_usd", "spot"])
        hist = pd.concat([hist, pd.DataFrame([{
            "date": today, "tonnes": round(tonnes, 2),
            "aum_usd": total_assets, "spot": spot
        }])], ignore_index=True).drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
        _db_sync("gld_holdings", lambda h=hist: db.sync_table("gld_holdings", h))

        wk_chg = round(tonnes - float(hist.iloc[-6]["tonnes"]), 2) if len(hist) >= 6 else None
        mo_chg = round(tonnes - float(hist.iloc[-21]["tonnes"]), 2) if len(hist) >= 21 else None
        return {"date": today, "tonnes": round(tonnes, 2),
                "wk_chg": wk_chg, "mo_chg": mo_chg,
                "aum_usd": round(total_assets / 1e9, 2)}
    except Exception as e:
        return {"error": str(e)}

def fetch_dxy(force=False):
    """ICE DXY via yfinance DX-Y.NYB. Syncs market_series; CSV is cold-start fallback."""
    try:
        DXY_CSV.parent.mkdir(parents=True, exist_ok=True)
        # always pull last 90d, dedupe + merge
        h = yf.Ticker("DX-Y.NYB").history(period="90d")
        if h.empty:
            return {"error": "yfinance empty"}
        new = pd.DataFrame({
            "date": h.index.strftime("%Y-%m-%d"),
            "value": h["Close"].round(3).values,
        })
        prior = db.read_slice("market_series", {"source": "yahoo", "symbol": "DXY"},
                              ["date", "value"]) if db else None
        if (prior is None or prior.empty) and DXY_CSV.exists():
            prior = pd.read_csv(DXY_CSV)[["date", "value"]]
        if prior is not None and not prior.empty and not force:
            combined = (pd.concat([prior, new], ignore_index=True)
                        .drop_duplicates("date", keep="last")
                        .sort_values("date").reset_index(drop=True))
        else:
            combined = new
        _db_sync("market_series:yahoo:DXY", lambda c=combined: db.sync_slice(
            "market_series", {"source": "yahoo", "symbol": "DXY"},
            c.assign(source="yahoo", symbol="DXY")[["source", "symbol", "date", "value"]],
            index_cols=["source", "symbol", "date"]))
        return {"last_date": str(combined["date"].iloc[-1]), "value": float(combined["value"].iloc[-1]), "rows": len(combined)}
    except Exception as e:
        return {"error": str(e)}

# ── ECONOMIC CALENDAR (#1/#2 — Forex Factory free JSON) ───────────────────────

# Forex Factory free calendar (faireconomy.media) — NO API KEY. (Prior provider was premium-gated
# → "no access" on its free tier, so we moved to this key-free feed.) Each feed is a
# JSON array of {title, country (currency code), date (ISO+offset), impact, forecast, previous,
# (sometimes) actual}. We map currency→ISO-2 so check_econ_calendar.py reads it unchanged.
FF_CAL_URLS = {
    "lastweek": "https://nfs.faireconomy.media/ff_calendar_lastweek.json",
    "thisweek": "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "nextweek": "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
}
FF_CCY_TO_ISO = {"USD": "US", "EUR": "EU", "GBP": "GB", "JPY": "JP", "AUD": "AU",
                 "NZD": "NZ", "CAD": "CA", "CHF": "CH", "CNY": "CN"}


def fetch_econ_calendar(force=False, days_back=10, days_fwd=10):
    """Forex Factory free JSON (faireconomy.media) → data/econ_calendar/calendar.csv.
    NO API key. Pulls last/this/next week (~±10d), maps currency→ISO-2 country, converts each
    event time to UTC, and merges/dedups on date+country+event so a re-pull backfills `actual`
    where the feed provides it (feeds the #2 surprise). days_back/days_fwd kept for signature
    compatibility (the FF feeds are fixed-week). Non-fatal — /weekly web-search fallback covers gaps."""
    headers = {"User-Agent": "Mozilla/5.0 (trading-brain econ-calendar)"}
    recs, errors = [], []
    for tag, url in FF_CAL_URLS.items():
        try:
            r = requests.get(url, headers=headers, timeout=20)
            rows = r.json()
        except Exception as ex:
            errors.append(f"{tag}:{ex}")
            continue
        if not isinstance(rows, list):
            errors.append(f"{tag}:unexpected payload")
            continue
        for e in rows:
            raw_dt = str(e.get("date", "") or "")
            date_s, time_s = "", ""
            if raw_dt:
                try:
                    dt = datetime.fromisoformat(raw_dt).astimezone(timezone.utc)
                    date_s, time_s = dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
                except ValueError:
                    date_s = raw_dt[:10]
            ccy = str(e.get("country", "") or "").upper().strip()
            recs.append({
                "date": date_s, "time_utc": time_s,
                "country": FF_CCY_TO_ISO.get(ccy, ccy), "event": e.get("title", ""),
                "impact": e.get("impact", ""), "estimate": e.get("forecast", ""),
                "actual": e.get("actual", ""), "prev": e.get("previous", ""),
                "unit": "",
            })
    if not recs:
        return {"error": f"FF calendar fetch failed ({'; '.join(errors) or 'no rows'})"}
    new = pd.DataFrame(recs, columns=ECON_COLS)
    new = new[new["date"].astype(str).str.len() == 10]   # drop unparseable dates
    ECON_DIR.mkdir(parents=True, exist_ok=True)
    if not force:
        old = db.read_table("econ_calendar") if db else None
        if (old is None or old.empty) and ECON_CSV.exists():
            old = pd.read_csv(ECON_CSV, dtype=str).fillna("")
        if old is not None and not old.empty:
            new = pd.concat([old[ECON_COLS], new.astype(str)], ignore_index=True)
    new = (new.astype(str)
           .drop_duplicates(["date", "country", "event"], keep="last")
           .sort_values(["date", "time_utc"]).reset_index(drop=True))
    _db_sync("econ_calendar", lambda n=new: db.sync_table("econ_calendar", n))
    return {"rows": len(new), "this_pull": len(recs), "source": "faireconomy(FF)",
            "last": new["date"].iloc[-1] if len(new) else "?",
            "warn": ("partial: " + "; ".join(errors)) if errors else ""}

# ── NEWS STORE (free RSS feeds — no API key, D025; key-free feed since 2026-06-15) ──

# Key-free forex/markets RSS, matching the key-free Forex Factory calendar feed. Standard RSS 2.0 <item>{title,link,pubDate,description?}. Reachable
# from the scheduled-task sandbox (DailyFX 403s, ForexLive 301s → excluded). check_news.py
# filters on headline text, so the item titles drive relevance.
NEWS_RSS_SOURCES = [
    ("FXStreet",      "forex", "https://www.fxstreet.com/rss/news"),
    ("Investing.com", "forex", "https://www.investing.com/rss/news_1.rss"),
]
# currency tags for the `related` column (schema parity; relevance filtering uses headline text)
_NEWS_REL_KW = {
    "XAU": ["gold", "bullion", "xau"],
    "USD": ["dollar", "fed", "fomc", "powell", "treasury"],
    "EUR": ["euro", "ecb", "eurozone", "lagarde"],
    "GBP": ["pound", "sterling", "boe", "gilt"],
    "JPY": ["yen", "boj", "mof", "ueda", "intervention"],
    "AUD": ["aussie", "australian dollar", "rba", "iron ore"],
    "NZD": ["kiwi", "new zealand", "rbnz", "dairy"],
    "CAD": ["loonie", "canadian dollar", "boc", "crude", "wti", " oil"],
    "CHF": ["franc", "swiss", "snb"],
}


def _parse_rss_date(s):
    """RSS pubDate → 'YYYY-MM-DDTHH:MM:SSZ' (UTC). Handles RFC822 (FXStreet, incl. bare 'Z')
    and ISO-ish 'YYYY-MM-DD HH:MM:SS' (Investing.com). Naive timestamps assumed UTC."""
    from email.utils import parsedate_to_datetime
    s = (s or "").strip()
    for f in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S Z",
              "%a, %d %b %Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(s, f)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return ""


def _derive_related(text):
    t = (text or "").lower()
    return ",".join(c for c, kws in _NEWS_REL_KW.items() if any(k in t for k in kws))


def fetch_news(force=False, categories=None):
    """Free RSS forex/markets feeds → data/news/headlines.csv (deduped on url). Accumulates a
    cross-week corpus for Section 2 + the Step 2b retrospective. Key-free since 2026-06-15
    (matches the FF calendar feed). `categories` kept for signature compatibility
    (unused). Non-fatal on failure — /weekly web-search fallback covers gaps."""
    import xml.etree.ElementTree as ET
    headers = {"User-Agent": "Mozilla/5.0 (trading-brain news)"}
    recs, errors = [], []
    for source, cat, url in NEWS_RSS_SOURCES:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            root = ET.fromstring(r.content)
        except Exception as ex:
            errors.append(f"{source}:{ex}")
            continue
        for it in root.iter("item"):
            def g(tag):
                el = it.find(tag)
                return (el.text or "").strip() if el is not None and el.text else ""
            title, link = g("title"), g("link")
            if not title or not link:
                continue
            summary = g("description")[:400]
            recs.append({"datetime_utc": _parse_rss_date(g("pubDate")), "category": cat,
                         "headline": title, "source": source, "url": link,
                         "summary": summary, "related": _derive_related(title + " " + summary)})
    if not recs:
        return {"error": f"RSS news fetch failed ({'; '.join(errors) or 'no rows'})"}
    new = pd.DataFrame(recs, columns=NEWS_COLS)
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    if not force:
        old = db.read_table("news") if db else None
        if (old is None or old.empty) and NEWS_CSV.exists():
            old = pd.read_csv(NEWS_CSV, dtype=str).fillna("")
        if old is not None and not old.empty:
            new = (pd.concat([old[NEWS_COLS], new.astype(str)], ignore_index=True)
                   .drop_duplicates("url", keep="last")
                   .sort_values("datetime_utc").reset_index(drop=True))
    _db_sync("news", lambda n=new: db.sync_table("news", n))
    return {"rows": len(new), "this_pull": len(recs),
            "source": "rss(" + "+".join(s for s, _, _ in NEWS_RSS_SOURCES) + ")",
            "last": new["datetime_utc"].max() if len(new) else "?",
            "warn": ("partial: " + "; ".join(errors)) if errors else ""}

# ── INTERMARKET COMMODITIES (#3 — yfinance, AUD/NZD only) ─────────────────────

def fetch_commodities_yf(tickers: dict):
    """Daily close for yfinance commodity tickers. Syncs market_series; CSV is fallback only."""
    out = {}
    COMMODITIES_DIR.mkdir(parents=True, exist_ok=True)
    for name, tk in tickers.items():
        try:
            h = yf.Ticker(tk).history(period="120d")
            if h.empty:
                out[name] = {"error": "empty"}; continue
            new = pd.DataFrame({"date": h.index.strftime("%Y-%m-%d"),
                                "value": h["Close"].round(4).values})
            p = COMMODITIES_DIR / f"{name}.csv"
            prior = db.read_slice("market_series", {"source": "commodities", "symbol": name},
                                  ["date", "value"]) if db else None
            if (prior is None or prior.empty) and p.exists():
                prior = pd.read_csv(p)[["date", "value"]]
            if prior is not None and not prior.empty:
                new = (pd.concat([prior, new], ignore_index=True)
                       .drop_duplicates("date", keep="last")
                       .sort_values("date").reset_index(drop=True))
            _db_sync(f"market_series:commodities:{name}", lambda n=new, nm=name: db.sync_slice(
                "market_series", {"source": "commodities", "symbol": nm},
                n.assign(source="commodities", symbol=nm)[["source", "symbol", "date", "value"]],
                index_cols=["source", "symbol", "date"]))
            out[name] = {"rows": len(new), "last": new["date"].iloc[-1],
                         "value": float(new["value"].iloc[-1])}
        except Exception as ex:
            out[name] = {"error": str(ex)}
    return out

# ── MAIN ──────────────────────────────────────────────────────────────────────

def fetch_and_update(force=False):
    """Fetch 15M bars, resample, update DB-backed data. Returns brief status lines.
    Called by both run() and --fetch-only mode (used by /validate)."""
    if not TWELVE_KEY or not FRED_KEY:
        print("ERROR: TWELVE_DATA_KEY or FRED_KEY not set in .env"); sys.exit(1)

    start_issue_count = len(RUN_ISSUES)
    print("Fetching 15M bars from Twelve Data (1 API call)...")
    new_15m  = fetch_15m(force=force)
    info_15m = upsert("twelvedata", SYMBOL, "15min", new_15m)
    print(f"  → {len(new_15m)} new 15M bars | last: {info_15m.get('last_dt', 'n/a (already current)')}")
    print("Resampling 15min → 1h / 4h / 1day...")
    resample_results = resample_all()
    for tf, rows, last in resample_results:
        print(f"  → {tf}: {rows} rows | last: {last}")
    print("Updating FRED macro series...")
    fred_results = update_fred(force=force)
    for sid, n, last in fred_results:
        print(f"  → {sid}: {n} new | last: {last}")
    print("Updating DXY (ICE 6-currency, yfinance DX-Y.NYB)...")
    dxy_res = _shared_result("dxy", force, lambda: fetch_dxy(force=force))
    if "error" in dxy_res:
        _record_issue("dxy", dxy_res["error"])
        print(f"  → DXY fetch FAILED: {dxy_res['error']}")
    else:
        print(f"  → DXY: {dxy_res['rows']} rows | last {dxy_res['last_date']} = {dxy_res['value']}")

    # Economic calendar (#1/#2) — shared across instruments, one CSV. Non-fatal on failure.
    print("Updating economic calendar (Forex Factory free JSON)...")
    econ_res = _shared_result("econ_calendar", force, lambda: fetch_econ_calendar(force=force))
    if "error" in econ_res:
        _record_issue("econ", econ_res["error"])
        print(f"  → econ calendar SKIPPED: {econ_res['error']} (kept previous DB rows; web-search fallback still applies)")
    else:
        warn = f" [{econ_res['warn']}]" if econ_res.get("warn") else ""
        print(f"  → econ calendar: {econ_res['rows']} rows ({econ_res['this_pull']} this pull), last {econ_res['last']}{warn}")

    # News store (free RSS feeds) — shared across instruments, one CSV. Non-fatal.
    print("Updating news store (RSS)...")
    news_res = _shared_result("news", force, lambda: fetch_news(force=force))
    if "error" in news_res:
        _record_issue("news", news_res["error"])
        print(f"  → news SKIPPED: {news_res['error']} (kept previous DB rows; web-search fallback still applies)")
    else:
        warn = f" [{news_res['warn']}]" if news_res.get("warn") else ""
        print(f"  → news: {news_res['rows']} rows ({news_res['this_pull']} this pull), last {news_res['last']}{warn}")

    # Intermarket commodities (#3) — only pairs that declare them (AUD/NZD).
    cfg = _instrument_cfg
    com_fred = list(getattr(cfg, "COMMODITY_FRED", []) or [])
    com_yf   = dict(getattr(cfg, "COMMODITY_YF", {}) or {})
    if com_fred:
        print(f"Updating commodity FRED series {com_fred}...")
        for sid, n, last in update_fred(force=force, series=com_fred):
            print(f"  → {sid}: {n} new | last: {last}")
    if com_yf:
        print(f"Updating commodity yfinance series {list(com_yf)}...")
        for name, info in fetch_commodities_yf(com_yf).items():
            if info.get("error"):
                _record_issue("commodity", f"{name} failed: {info['error']}")
            print(f"  → {name}: {info.get('error') or str(info.get('value')) + ' (' + str(info.get('rows')) + ' rows)'}")

    # Positioning (COT) → `cot` table; ETF flows → `gld_holdings` table. Both DB-canonical,
    # read back by the MCP get_zone_context tool. Non-fatal on failure.
    if cfg is None or cfg.COT_ENABLED:
        print("  → COT (CFTC)...")
        cot = fetch_cot()
        if isinstance(cot, dict) and "error" not in cot:
            contract = (cfg.COT_CONTRACT_NAME if cfg else "GOLD - COMMODITY EXCHANGE INC.")
            row = pd.DataFrame([{"contract": contract, "date": cot["date"],
                                 "long": cot["long"], "short": cot["short"],
                                 "net": cot["net"], "net_prev": cot.get("net_prev")}])
            _db_sync(f"cot:{contract}", lambda r=row, c=contract: db.sync_slice(
                "cot", {"contract": c}, r))
        elif isinstance(cot, dict) and "error" in cot:
            _record_issue("cot", cot["error"])
            print(f"  → COT skipped: {cot['error']}")

    if cfg is None or cfg.ETF_ENABLED:
        print(f"  → ETF flows ({cfg.ETF_TICKER if cfg else 'GLD'})...")
        etf = fetch_gld_flows()   # syncs the `gld_holdings` table internally
        if isinstance(etf, dict) and "error" in etf:
            _record_issue("etf", etf["error"])
            print(f"  → ETF flows skipped: {etf['error']}")

    _print_health(start_issue_count)
    return info_15m


def run(force=False):
    """Fetch every source and sync it to the canonical DB. The AI leg reads the result
    back through MCP (get_zone_context / sql_query) — no snapshot file is written."""
    fetch_and_update(force=force)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Re-fetch full history")
    ap.add_argument("--instrument", default="xauusd",
                    choices=list(REGISTERED_INSTRUMENTS) + ["all"],
                    help="Instrument to run (default: xauusd). 'all' runs every registered instrument.")
    args = ap.parse_args()

    to_run = list(REGISTERED_INSTRUMENTS) if args.instrument == "all" else [args.instrument]
    for i, inst in enumerate(to_run):
        if len(to_run) > 1:
            print(f"\n{'='*54}\n  {inst.upper()}\n{'='*54}")
        # TwelveData free tier = 8 API credits/minute; an unpaced 11-pair loop blows through
        # it mid-run, so tail instruments error/retry on a later minute and land on a
        # different hourly bar than the head instruments (observed as a multi-hour OHLC
        # freshness stagger across pairs). 9s spacing keeps fetches under the per-minute cap.
        if i > 0 and len(to_run) > 1:
            time.sleep(9)
        load_instrument(inst)
        try:
            run(force=args.force)
        except Exception as exc:
            _record_issue("fetch", f"{inst} aborted: {exc}")
            print(f"❌ {inst.upper()} aborted: {exc}")
            if len(to_run) == 1:
                raise

    critical = [issue for issue in RUN_ISSUES if _is_critical_issue(issue)]
    if RUN_ISSUES and len(to_run) > 1:
        print(f"\nRun health: issues={len(RUN_ISSUES)}, critical={len(critical)}")
        for issue in RUN_ISSUES[:20]:
            print(f"  - {issue}")
        if len(RUN_ISSUES) > 20:
            print(f"  - ... {len(RUN_ISSUES) - 20} more")
    if critical:
        sys.exit(2)
