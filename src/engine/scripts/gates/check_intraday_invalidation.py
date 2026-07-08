"""
Intraday H4 invalidation checker — constitution rule H4_BUFFER_BREAK (markdown-only, no DB).

Checks the last 2 H4 closes in data/twelvedata/{instrument}/4h.csv against a
trading-zone extreme. Flags 2 consecutive H4 closes >BUFFER past the zone =
intraday invalidation (cancel limit before D1 close confirms).

BUFFER defaults to ATR-SCALED (0.25 x H4 ATR14, computed on closed bars) instead
of a static per-pair pip constant — a fixed buffer whipsaws high-ATR pairs
(gbpjpy's static 0.05 cancelled a running +1R W27 winner on a 20-pip H4 breach,
~2-3% of its H4 ATR). Pass --buffer to override with a static value (old behavior).

Zone is passed on the CLI by /validate (the active zone comes from the `zone_ledger`
DB table, read via MCP get_brief). Run at each H4 boundary (00/04/08/12/16/20 UTC).

Usage:
    bash scripts/pyrun.sh scripts/gates/check_intraday_invalidation.py --direction SHORT --zone-top 3400 --zone-bottom 3380
    bash scripts/pyrun.sh scripts/gates/check_intraday_invalidation.py --direction LONG  --zone-top 3300 --zone-bottom 3280 --buffer 5
    bash scripts/pyrun.sh scripts/gates/check_intraday_invalidation.py --direction SHORT --zone-top 215.6 --zone-bottom 215.0 --atr-mult 0.25

Exit codes: 0 intact / 2 breach.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts root, for `db` import


def atr14_before(df: pd.DataFrame, cutoff: pd.Timestamp):
    """ATR(14) on bars with datetime strictly before cutoff. None if <15 bars."""
    d = df[df["datetime"] < cutoff]
    if len(d) < 15:
        return None
    h, l, c = d["high"], d["low"], d["close"]
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(14).mean().iloc[-1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instrument", default="xauusd")
    parser.add_argument("--direction", required=True, choices=["LONG", "SHORT"])
    parser.add_argument("--zone-top", type=float, required=True)
    parser.add_argument("--zone-bottom", type=float, required=True)
    parser.add_argument("--buffer", type=float, default=None,
                        help="static buffer past zone extreme that counts as a real breach "
                             "(overrides --atr-mult if given)")
    parser.add_argument("--atr-mult", type=float, default=0.25,
                        help="buffer = atr-mult x H4 ATR14 when --buffer not given (default 0.25)")
    parser.add_argument("--label", default="", help="optional zone label for output")
    args = parser.parse_args()

    h4 = None
    try:
        import db
        h4 = db.read_ohlc(args.instrument, "4h")          # canonical store
    except Exception:
        h4 = None
    if h4 is None or h4.empty:
        h4_csv = Path(f"data/twelvedata/{args.instrument}/4h.csv")   # CSV fallback
        if not h4_csv.exists():
            print(f"❌ Missing {h4_csv}")
            sys.exit(1)
        h4 = pd.read_csv(h4_csv)
    h4 = h4.copy()
    h4["datetime"] = pd.to_datetime(h4["datetime"])
    for c in ["open", "high", "low", "close"]:
        if c in h4.columns:
            h4[c] = pd.to_numeric(h4[c], errors="coerce")
    h4 = h4.sort_values("datetime")
    last2 = h4.tail(2)
    if len(last2) < 2:
        print("Not enough H4 bars.")
        return

    c1, c2 = float(last2["close"].iloc[0]), float(last2["close"].iloc[1])

    if args.buffer is not None:
        buf = args.buffer
        buf_src = "static"
    else:
        h4_atr = atr14_before(h4, h4["datetime"].iloc[-1])
        if h4_atr is None:
            buf, buf_src = 5.0, "fallback (insufficient H4 history for ATR)"
        else:
            buf, buf_src = args.atr_mult * h4_atr, f"{args.atr_mult}xH4ATR14={h4_atr:.5g}"

    # Display precision: $-scale (gold, >=500) 2dp; JPY-scale (20–500, pip 0.01) 3dp; pip-scale FX 5dp.
    dp = 2 if args.zone_top >= 500 else (3 if args.zone_top >= 20 else 5)
    print(f"H4_BUFFER_BREAK check ({args.instrument}{' ' + args.label if args.label else ''}) — buffer {buf:.{dp}f} ({buf_src})")
    print(f"  last 2 H4 closes: "
          f"{c1:.{dp}f} @ {last2['datetime'].iloc[0]} | "
          f"{c2:.{dp}f} @ {last2['datetime'].iloc[1]}")

    if args.direction == "SHORT":
        extreme = args.zone_top + buf
        breach = (c1 > extreme) and (c2 > extreme)
    else:
        extreme = args.zone_bottom - buf
        breach = (c1 < extreme) and (c2 < extreme)

    verdict = "❌ H4_BUFFER_BREAK BREACH — INVALIDATE" if breach else "✅ intact"
    print(f"{args.direction} zone {args.zone_bottom:.{dp}f}–{args.zone_top:.{dp}f} | "
          f"threshold {extreme:.{dp}f} | {verdict}")

    if breach:
        print("\n→ Cancel live limit for this zone (write_verdict CANCEL_LIMIT via MCP).")
        sys.exit(2)


if __name__ == "__main__":
    main()
