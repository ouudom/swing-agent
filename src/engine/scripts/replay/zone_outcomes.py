"""
Zone outcomes — shadow-trade resolver. Replays stored OHLC against every zone in the
`zone_ledger` DB table and writes would-be results to the `zone_outcome` table
(SL = zone width) and the `zone_atr_sl_outcome` comparison table (SL = constitution
ATR formula). Only `zone_outcome` drives `zone_ledger.status`.

Answers, per published zone: did price reach it? would the trade have won? After
~20–30 resolved zones the summary shows whether Zone Confluence 8.0 actually beats
6.5 — outcome data the live system cannot produce while zones get blocked (V3) or
expire untouched.

Shadow-trade model (simplifications, deliberately documented):
  - Fill   = first 1H bar inside the trade week (Mon 00:00 → Fri 22:00 UTC) whose
             range crosses the ZONE NEAR EDGE (top for LONG, bottom for SHORT —
             the edge price hits first on approach into the zone). Entry price =
             that edge. No E0/offset replay — this measures ZONE quality, not
             entry-timing quality (that's R2's job).
  - Kill   = D1 close beyond invalidation_level (ledger value, else zone far edge)
             before fill → INVALIDATED. D1 close treated as effective at
             bar_date + 22:00 UTC (FX session close).
  - SL     = zone_top − zone_bottom (the zone's own width, `sl_mode="zone"`, default
             — entry sits at the near edge so this stop lands exactly on the far
             edge). The `zone_atr_sl_outcome` table instead resolves with
             `sl_mode="atr"`: constitution formula H4_ATR14 if 0.5×D1_ATR14 <
             H4_ATR14 else avg(0.5×D1_ATR14, H4_ATR14); comparison only, does not
             drive the ledger. H4_ATR14 is mandatory; D1_ATR14 is optional and
             falls back to H4-only if unusable (too few bars, or a NaN mean from
             a gappy D1 bar) — a bad D1 print shouldn't block a zone that has a
             perfectly good H4 series.
  - Manage = TP +3.0R nearer zone / +4.0R further zone (v3 distance-tiered); SL −1R;
             BE: stop → entry after a bar's MFE reaches +1.5R
             (armed from the NEXT bar). Same-bar SL+TP ambiguity → SL (conservative).
             Walk is unbounded past the forecast week — a filled trade keeps
             running until it actually exits (matches constitution: filled
             positions run past Friday's cancel-unfilled-limits cutoff).
  - Status = PENDING (week live, no fill yet) | NO_TOUCH | TOUCH_NO_FILL |
             INVALIDATED | WIN_TP1 | LOSS_SL | BREAKEVEN | RUNNING.
             At the zone's own market close (Fri 22:00 UTC), every zone that isn't
             filled-and-still-live resolves to a terminal status; a filled zone
             that hasn't hit TP/SL/BE stays RUNNING regardless of market close and
             is re-resolved on the next run. Terminal statuses flip the ledger row
             to RESOLVED; RUNNING (and PENDING) leave it OPEN.

Usage:
    bash scripts/pyrun.sh scripts/replay/zone_outcomes.py            # resolve all + summary
    bash scripts/pyrun.sh scripts/replay/zone_outcomes.py --week 2026-W24
    bash scripts/pyrun.sh scripts/replay/zone_outcomes.py --only atr # zone_atr_sl_outcome only
"""

from __future__ import annotations

import argparse
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts root, for `db`/`config.*` imports

import db  # noqa: E402
from zone_ledger import load_ledger, save_ledger  # noqa: E402

OUTCOMES_TABLE = "zone_outcome"          # sl_mode="zone" — drives zone_ledger.status
ATR_TABLE = "zone_atr_sl_outcome"        # sl_mode="atr"  — comparison only
TERMINAL = {"NO_TOUCH", "TOUCH_NO_FILL", "INVALIDATED", "WIN_TP1", "LOSS_SL", "BREAKEVEN"}

# v3 distance-tiered TP (matches trade_outcome.py): within each (instrument, week) the zone
# nearest the week's opening spot targets 3.0R, all others 4.0R. Replaces the flat TP1 2.5R.
TP_R_NEAR = 3.0
TP_R_FAR = 4.0

# R1 (zone_confluence) buckets, shared with calibration.py. (label, lo_inclusive, hi_exclusive).
R1_BUCKETS = [(">=8.0", 8.0, 99.0), ("7.0–7.9", 7.0, 8.0), ("<7.0", 0.0, 7.0)]
# Completed = a shadow trade that actually filled and reached a terminal R outcome.
COMPLETED_STATUSES = ["WIN_TP1", "LOSS_SL", "BREAKEVEN"]

OUT_COLS = [
    "zone_id", "instrument", "week", "label", "direction", "zone_confluence",
    "conviction", "status", "touched", "fill_time", "entry", "sl_dist",
    "r_result", "mfe_r", "mae_r", "exit_time", "resolved_utc",
]


def week_window(week: str):
    """'2026-W24' → (Mon 00:00 UTC, Fri 22:00 UTC) as naive UTC timestamps."""
    year, wnum = week.split("-W")
    mon = datetime.fromisocalendar(int(year), int(wnum), 1)
    start = pd.Timestamp(mon)
    return start, start + pd.Timedelta(days=4, hours=22)


def atr14_before(df: pd.DataFrame, cutoff: pd.Timestamp):
    """ATR(14) on bars with datetime strictly before cutoff. None if <15 bars."""
    d = df[df["datetime"] < cutoff]
    if len(d) < 15:
        return None
    h, l, c = d["high"], d["low"], d["close"]
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(14).mean().iloc[-1])


def load_tf(instrument: str, tf: str) -> pd.DataFrame:
    df = db.read_ohlc(instrument, tf)        # canonical; CSV fallback for cold start
    if df is None or df.empty:
        p = Path(f"data/twelvedata/{instrument}/{tf}.csv")
        if not p.exists():
            raise FileNotFoundError(p)
        df = pd.read_csv(p)
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    for c in ["open", "high", "low", "close", "volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("datetime").reset_index(drop=True)


def min_bar_range(instrument: str) -> float:
    cfg = importlib.import_module(f"config.{instrument}")
    return float(getattr(cfg, "MIN_BAR_RANGE", 0.0))


def resolve_zone(z: pd.Series, h1: pd.DataFrame, h4: pd.DataFrame, d1: pd.DataFrame,
                 mbr: float, tp_r: float = TP_R_NEAR, sl_mode: str = "zone") -> dict:
    out = {c: "" for c in OUT_COLS}
    out.update({k: z[k] for k in ["zone_id", "instrument", "week", "label", "direction",
                                  "zone_confluence", "conviction"]})
    start, end = week_window(z["week"])
    top, bot = float(z["zone_top"]), float(z["zone_bottom"])
    sign = 1 if z["direction"] == "LONG" else -1
    entry_px = top if sign > 0 else bot  # near edge: first hit on approach into the zone
    inval = z["invalidation_level"]
    inval = float(inval) if str(inval) not in ("", "nan") else (top if sign < 0 else bot)

    # Real wall-clock, not last-bar-time: FX has no bars Fri ~21:00-Mon open, so a
    # last-bar proxy would keep week_live True over the whole weekend gap.
    wall_now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    week_live = wall_now < end

    # invalidation: first D1 close beyond kill level, effective at date+22:00 UTC
    dwin = d1[(d1["datetime"] >= start - pd.Timedelta(days=1))]
    if sign < 0:
        killed = dwin[dwin["close"] > inval]
    else:
        killed = dwin[dwin["close"] < inval]
    kill_time = (killed["datetime"].iloc[0] + pd.Timedelta(hours=22)) if not killed.empty else None
    if kill_time is not None and kill_time > end:
        kill_time = None  # zone expires at week end anyway

    # fills only count from publish time — mid-week forecasts must not look back
    if str(z["published_utc"]) not in ("", "nan"):
        pub = pd.Timestamp(str(z["published_utc"]))
        if pub.tz is not None:
            pub = pub.tz_convert("UTC").tz_localize(None)
    else:
        pub = start
    live_from = max(start, pub)
    win = h1[(h1["datetime"] >= live_from) & (h1["datetime"] < end)]
    if kill_time is not None:
        win = win[win["datetime"] < kill_time]

    touched = win[(win["low"] <= top) & (win["high"] >= bot)]
    filled = win[(win["low"] <= entry_px) & (win["high"] >= entry_px)]
    out["touched"] = bool(len(touched))

    if filled.empty:
        if kill_time is not None:
            out["status"] = "INVALIDATED"
        elif week_live:
            out["status"] = "PENDING"
        else:
            out["status"] = "TOUCH_NO_FILL" if len(touched) else "NO_TOUCH"
        return out

    fill_bar = filled.iloc[0]
    fill_time = fill_bar["datetime"]
    out["fill_time"], out["entry"] = str(fill_time), entry_px

    if sl_mode == "atr":
        d1_atr = atr14_before(d1, pd.Timestamp(fill_time.date()))
        h4_trade = h4[(h4["high"] - h4["low"]) >= mbr]
        h4_atr = atr14_before(h4_trade, fill_time)
        # pd.isna catches both "too few bars" (None) and a NaN mean from gappy OHLC.
        # H4 is mandatory (no other SL source); D1 is optional — if it's unusable
        # (e.g. a NULL-OHLC day poisoning its rolling window) fall back to H4_ATR14
        # alone rather than blocking the whole zone on a bad D1 bar.
        if pd.isna(h4_atr):
            out["status"] = "PENDING"
            out["fill_time"] = ""
            return out
        sl = h4_atr if pd.isna(d1_atr) or 0.5 * d1_atr < h4_atr else (0.5 * d1_atr + h4_atr) / 2
    else:  # "zone" — SL is the zone's own width; entry at near edge → stop at far edge
        sl = top - bot
    out["sl_dist"] = round(sl, 6)

    stop = entry_px - sign * sl
    tp = entry_px + sign * tp_r * sl
    be_trigger = entry_px + sign * 1.5 * sl
    be_armed = False
    mfe = mae = 0.0

    walk = h1[h1["datetime"] >= fill_time]  # unbounded — filled trades run past the forecast week
    for _, bar in walk.iterrows():
        hi, lo = bar["high"], bar["low"]
        fav = (hi - entry_px) if sign > 0 else (entry_px - lo)
        adv = (entry_px - lo) if sign > 0 else (hi - entry_px)
        mfe, mae = max(mfe, fav / sl), max(mae, adv / sl)

        stopped = lo <= stop if sign > 0 else hi >= stop
        hit_tp = hi >= tp if sign > 0 else lo <= tp
        if stopped:  # same-bar ambiguity → stop first (conservative)
            out["status"] = "BREAKEVEN" if be_armed and stop == entry_px else "LOSS_SL"
            out["r_result"] = 0.0 if out["status"] == "BREAKEVEN" else -1.0
            out["exit_time"] = str(bar["datetime"])
            break
        if hit_tp:
            out["status"], out["r_result"] = "WIN_TP1", tp_r
            out["exit_time"] = str(bar["datetime"])
            break
        if not be_armed and (hi >= be_trigger if sign > 0 else lo <= be_trigger):
            be_armed = True
            stop = entry_px  # armed; effective next bar (this bar's stop already checked)
    else:
        out["status"] = "RUNNING"  # not yet resolved — re-resolved next run regardless of market close
        last_close = walk["close"].iloc[-1] if len(walk) else entry_px
        out["r_result"] = round(sign * (last_close - entry_px) / sl, 2)

    out["mfe_r"], out["mae_r"] = round(mfe, 2), round(mae, 2)
    return out


def summarize(df: pd.DataFrame):
    print("\n── Zone outcome summary " + "─" * 40)
    print(df["status"].value_counts().to_string())
    done = df[df["status"].isin(COMPLETED_STATUSES)]
    if done.empty:
        print("\nNo completed shadow trades yet.")
        return
    r = pd.to_numeric(done["r_result"])
    wins = (done["status"] == "WIN_TP1").sum()
    print(f"\nCompleted: {len(done)} | wins {wins} ({wins / len(done):.0%}) | "
          f"total {r.sum():+.1f}R | avg {r.mean():+.2f}R")
    score = pd.to_numeric(done["zone_confluence"])
    for lbl, lo, hi in R1_BUCKETS:
        m = (score >= lo) & (score < hi)
        n = m.sum()
        if n:
            w = ((done["status"] == "WIN_TP1") & m).sum()
            print(f"  R1 {lbl}: n={n} win {w / n:.0%} avg {r[m].mean():+.2f}R")


def run_replay(table: str, sl_mode: str, week: str = "", instrument: str = "",
               update_ledger: bool = False, wipe: bool = False) -> pd.DataFrame:
    """Resolve every ledger zone (optionally filtered) into `table` using `sl_mode`.

    wipe=True writes exactly this run's rows with no merge against prior contents —
    use for a full rebuild after a rule change breaks comparability with old rows.
    update_ledger=True additionally flips zone_ledger.status from this run's results
    (only zone_outcome / sl_mode="zone" should own the ledger).
    """
    ledger = load_ledger()
    if ledger.empty:
        sys.exit("ledger empty — register zones with zone_ledger.py first")
    todo = ledger.copy()
    if week:
        todo = todo[todo["week"] == week]
    if instrument:
        todo = todo[todo["instrument"] == instrument]

    rows, data_cache = [], {}

    def _h1(inst):
        if inst not in data_cache:
            data_cache[inst] = (load_tf(inst, "1h"), load_tf(inst, "4h"),
                                load_tf(inst, "1day"), min_bar_range(inst))
        return data_cache[inst][0]

    # v3 distance-tiered TP: nearest zone to the week's opening spot → 3.0R, others → 4.0R.
    tp_r_map = {}
    for (inst, wk), grp in todo.groupby(["instrument", "week"]):
        wstart, _ = week_window(wk)
        sb = _h1(inst)[_h1(inst)["datetime"] >= wstart]
        spot = float(sb["close"].iloc[0]) if not sb.empty else None
        dists = {z["zone_id"]: (abs((float(z["zone_top"]) + float(z["zone_bottom"])) / 2 - spot)
                                if spot is not None else 0.0)
                 for _, z in grp.iterrows()}
        nearest = min(dists, key=dists.get)
        for zid in dists:
            tp_r_map[zid] = TP_R_NEAR if zid == nearest else TP_R_FAR

    for _, z in todo.iterrows():
        inst = z["instrument"]
        if inst not in data_cache:
            data_cache[inst] = (load_tf(inst, "1h"), load_tf(inst, "4h"),
                                load_tf(inst, "1day"), min_bar_range(inst))
        h1, h4, d1, mbr = data_cache[inst]
        out = resolve_zone(z, h1, h4, d1, mbr, tp_r=tp_r_map.get(z["zone_id"], TP_R_NEAR),
                           sl_mode=sl_mode)
        out["resolved_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append(out)
        if update_ledger:
            ledger.loc[ledger["zone_id"] == z["zone_id"], "status"] = (
                "RESOLVED" if out["status"] in TERMINAL else "OPEN")
        print(f"[{table}] {z['zone_id']:<32} {z['direction']:<5} "
              f"{z['zone_bottom']}–{z['zone_top']}  → {out['status']}"
              + (f" ({out['r_result']:+.1f}R)" if out["r_result"] != "" else ""))

    res = pd.DataFrame(rows)[OUT_COLS]
    if not wipe:
        old = db.read_table(table)  # keep rows for zones outside this run's filter
        if not old.empty and "zone_id" in old.columns:
            old = old[~old["zone_id"].isin(res["zone_id"])]
            if not old.empty:
                res = pd.concat([old.astype(str), res.astype(str)], ignore_index=True)
    db.write_table(table, res)
    if update_ledger:
        save_ledger(ledger)
    print(f"\n→ {table} table ({len(res)} rows)" + (" — ledger statuses updated" if update_ledger else ""))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--week", default="", help="resolve only this trade week")
    ap.add_argument("--instrument", default="")
    ap.add_argument("--only", choices=["both", "zone", "atr"], default="both",
                    help="which table(s) to resolve")
    args = ap.parse_args()

    if args.only in ("both", "zone"):
        res_zone = run_replay(OUTCOMES_TABLE, "zone", args.week, args.instrument, update_ledger=True)
        summarize(res_zone)

    if args.only in ("both", "atr"):
        res_atr = run_replay(ATR_TABLE, "atr", args.week, args.instrument, update_ledger=False)
        summarize(res_atr)


if __name__ == "__main__":
    main()
