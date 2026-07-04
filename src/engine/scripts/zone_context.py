"""
zone_context — assemble the deterministic zone-generation context for one instrument
straight from the canonical DB (Postgres), reusing the tested indicator/structure
libraries. This is the DB-native replacement for the write-only weekly_pull_*.txt dump:
the AI leg calls it over MCP (`get_zone_context`) to score Trading Zones at /weekly,
instead of reading a flat file the deployed app no longer needs.

Everything here is a pure function of data already in the DB — OHLC (`ohlc`), macro
(`macro_series`), market (`market_series`), positioning (`cot`). No network, no CSV,
no markdown. Indicators come from backtest_signals (the same library the replay/EC
path uses); structure/levels from structure.py. All indicators run on CLOSED bars only
(the forming period bar is dropped) so two runs the same day agree.
"""
from __future__ import annotations

import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts root: db, structure, backtest_signals

import config as config_pkg  # noqa: E402  (price_dp helper)
import db  # noqa: E402
import structure as st  # noqa: E402
from backtest_signals import (  # noqa: E402
    rsi, atr, adx, stoch_k, williams_r, cci, macd, bollinger, ema,
    load_fred, load_dxy, rolling_slope,
)

TFS = {"d1": "1day", "h4": "4h", "h1": "1h"}


def _load(inst: str, tf: str) -> pd.DataFrame:
    """DB OHLC → datetime-indexed numeric frame, sorted, de-duped. Empty frame if absent."""
    df = db.read_ohlc(inst, tf)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    for c in ("open", "high", "low", "close", "volume"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.set_index("datetime").sort_index()
    return df[~df.index.duplicated(keep="last")]


def _cfg(inst: str):
    return importlib.import_module(f"config.{inst}")


def _r(x, dp):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), dp)


def _momentum(df: pd.DataFrame, dp: int) -> dict:
    """Momentum/oscillator snapshot on CLOSED bars (drop the forming last bar)."""
    d = df.iloc[:-1]
    if len(d) < 30:
        return {}
    c = d["close"]
    line, sig = macd(c)
    up, lo, pctb, _ = bollinger(c)
    out = {
        "rsi14":   _r(rsi(c).iloc[-1], 1),
        "adx14":   _r(adx(d).iloc[-1], 1),
        "stoch_k": _r(stoch_k(d).iloc[-1], 1),
        "williams_r": _r(williams_r(d).iloc[-1], 1),
        "cci20":   _r(cci(d).iloc[-1], 1),
        "ema50":   _r(ema(c, 50).iloc[-1], dp),
        "ema200":  _r(ema(c, 200).iloc[-1], dp) if len(d) >= 200 else None,
        "macd":    _r(line.iloc[-1], dp),
        "macd_signal": _r(sig.iloc[-1], dp),
        "macd_hist": _r((line - sig).iloc[-1], dp),
        "boll_upper": _r(up.iloc[-1], dp),
        "boll_lower": _r(lo.iloc[-1], dp),
        "boll_pctb": _r(pctb.iloc[-1], 2),
    }
    return out


def _cot(inst: str, cfg) -> dict | None:
    """Latest COT positioning for the instrument's contract, from the `cot` table."""
    contract = getattr(cfg, "COT_CONTRACT_NAME", None)
    if not contract or not getattr(cfg, "COT_ENABLED", True):
        return None
    rows = db.read_slice("cot", {"contract": contract},
                         ["date", "long", "short", "net", "net_prev"])
    if rows is None or rows.empty:
        return None
    last = rows.iloc[-1]
    def _i(v):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None
    net, net_prev = _i(last["net"]), _i(last["net_prev"])
    return {
        "date": last["date"], "long": _i(last["long"]), "short": _i(last["short"]),
        "net": net, "net_prev": net_prev,
        "net_chg": (net - net_prev) if (net is not None and net_prev is not None) else None,
        "inverted": bool(getattr(cfg, "COT_INVERTED", False)),
    }


def build(instrument: str) -> dict:
    inst = instrument.lower()
    cfg = _cfg(inst)
    dp = config_pkg.price_dp(cfg)
    mbr = float(getattr(cfg, "MIN_BAR_RANGE", 0.0))

    d1, h4, h1 = (_load(inst, TFS[k]) for k in ("d1", "h4", "h1"))
    if d1.empty or h4.empty or h1.empty:
        missing = [TFS[k] for k, f in zip(("d1", "h4", "h1"), (d1, h4, h1)) if f.empty]
        return {"instrument": inst, "error": f"missing OHLC in DB: {', '.join(missing)} — run fetch_data"}

    d1c, h4c = d1.iloc[:-1], h4.iloc[:-1]        # closed-bar frames for ATR/structure
    spot = float(h1["close"].iloc[-1])

    # ATR (D1 full, H4 on trading-session bars only) + SL preview (constitution v3)
    d1_atr_s = atr(d1c).dropna()
    d1_atr = float(d1_atr_s.iloc[-1]) if len(d1_atr_s) else None
    h4_trade = h4c[(h4c["high"] - h4c["low"]) >= mbr]
    h4_atr_s = atr(h4_trade).dropna()
    h4_atr = float(h4_atr_s.iloc[-1]) if len(h4_atr_s) else None
    sl = None
    if d1_atr is not None and h4_atr is not None:
        sl = h4_atr if (0.5 * d1_atr) < h4_atr else (0.5 * d1_atr + h4_atr) / 2

    # structure / levels
    sh, sl_pts = st.swing_points(d1c, dp)
    sh_h4, sl_h4 = st.swing_points(h4c, dp)
    rec_hi = sh[-1][1] if sh else float(d1c["high"].tail(30).max())
    rec_lo = sl_pts[-1][1] if sl_pts else float(d1c["low"].tail(30).min())
    tap = st.time_at_price(h1, window=480)

    macro = {"dxy": None, "dxy_slope20": None, "dxy_chg5": None, "vix": None, "fred": {}}
    dxy = load_dxy()
    if dxy is not None and len(dxy) > 21:
        macro["dxy"] = _r(dxy.iloc[-1], 3)
        macro["dxy_slope20"] = _r(rolling_slope(dxy, 20).iloc[-1], 4)
        macro["dxy_chg5"] = _r((dxy.iloc[-1] / dxy.iloc[-6] - 1) * 100, 3)
    vix = load_fred("VIXCLS")
    if vix is not None and len(vix):
        macro["vix"] = _r(vix.iloc[-1], 2)
    for sid in getattr(cfg, "FRED_SERIES", []):
        s = load_fred(sid)
        if s is not None and len(s):
            macro["fred"][sid] = _r(s.iloc[-1], 4)

    return {
        "instrument": inst,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "spot": _r(spot, dp),
        "latest_bar": str(h1.index[-1]),
        "atr": {
            "d1_atr14": _r(d1_atr, dp), "h4_atr14": _r(h4_atr, dp),
            "d1_atr_now": _r(d1_atr, dp),
            "d1_atr_median20": _r(d1_atr_s.tail(20).median(), dp) if len(d1_atr_s) else None,
            "compressed": bool(len(d1_atr_s) and d1_atr < float(d1_atr_s.tail(20).median())),
        },
        "sl_preview": {"sl_dist": _r(sl, dp),
                       "rule": "H4_ATR14 if 0.5*D1_ATR14 < H4_ATR14 else avg(0.5*D1_ATR14, H4_ATR14)"},
        "structure": {
            "pivots": st.calc_pivots(d1c, dp),
            "fibs": st.fib_levels(rec_lo, rec_hi, dp),
            "swings_d1": {"highs": sh, "lows": sl_pts},
            "swings_h4": {"highs": sh_h4, "lows": sl_h4},
            "bos_choch_h4": st.structure_events(h4c),
            "time_at_price_h1": {k: _r(v, dp) for k, v in tap.items()} if tap else None,
        },
        "momentum_d1": _momentum(d1, dp),
        "momentum_h4": _momentum(h4, dp),
        "macro": macro,
        "positioning": _cot(inst, cfg),
    }


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description="Assemble DB-native zone context for one instrument.")
    ap.add_argument("--instrument", default="xauusd")
    print(json.dumps(build(ap.parse_args().instrument), indent=2, default=str))
