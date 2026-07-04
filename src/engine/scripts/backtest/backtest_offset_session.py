"""
Offset-by-session study — does the optimal outward-offset width depend on the SESSION
of the signal bar?

The live offset = max(SL/3, (10 − EC) × 0.2 × SL) is session-blind. But overshoot
behaviour (how far price pokes beyond the signal close before reversing) plausibly
differs by session: London-open stop-runs overshoot deep; Asia drifts and rarely
overshoots. If true, a session-conditioned offset multiplier fills more good trades
in quiet sessions and demands more commitment in violent ones.

Two studies over the full H1 history (2020–2026, DB `ohlc`):

  A. OVERSHOOT DISTRIBUTION — for every H1 oscillator-extreme TRANSITION bar (fade
     setup, same def as backtest_entry_sim), the max outward poke beyond the signal
     close within W_FILL bars, in s = H1 ATR14 units, grouped by signal-bar session.
     Quantiles answer: what offset does each session support at a given fill prob?

  B. OFFSET SWEEP × SESSION — LIMIT-arm sim (entry_sim harness): limit at f×s outward,
     f ∈ {0.33, 0.50, 0.70, 0.90, 1.00} (≈ EC 8.3 / 7.5 / 6.5 / 5.5 / 5.0 under the
     live formula), fill within W_FILL bars, walk ≤ MAX_HOLD to SL −1R / TP +2.5R.
     Key metric = expectancy PER SETUP (missed fill = 0R), the number the offset
     actually trades off. Optimal f per session = the session-conditioned formula.

Sessions (UTC bar-open hour): ASIA 22–06 | LONDON 07–11 | NY_OVLP 12–15 | NY_PM 16–21.
DST smears London/NY edges by 1h — buckets are coarse on purpose.

Caveats: FX mean-reversion fades; xauusd is continuation — reported separately, read
with suspicion. s here is H1 ATR14 (scale-invariant), live SL is H4-based; the f-axis
maps to EC via the live formula only approximately.

Usage:
  bash scripts/pyrun.sh scripts/backtest/backtest_offset_session.py
  bash scripts/pyrun.sh scripts/backtest/backtest_offset_session.py --wfill 24 --out wiki/research/general/offset-session-study.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "replay"))  # zone_outcomes.load_tf

from backtest_signals import (  # noqa: E402
    atr, rsi, stoch_k, williams_r, keltner,
    pin_bull, pin_bear, bull_engulf, bear_engulf, REGISTERED,
)
from zone_outcomes import load_tf  # noqa: E402  (DB loader — CSVs are gone)

W_FILL = 12
MAX_HOLD = 48
TP_R = 3.0                                        # v3: TP1 2.5R removed, single 3.0R target
FRACS = [0.15, 0.20, 0.30, 0.40, 0.50, 0.70, 1.00]   # test proposed 0.2/0.3/0.5 + neighbours
SESSIONS = ["ASIA", "LONDON", "NY"]               # NY = 12–21 UTC single bucket (owns overlap)


def session_of(hour: int) -> str:
    if 7 <= hour <= 11:
        return "LONDON"                          # 07:00–12:00 UTC
    if 12 <= hour <= 21:
        return "NY"                              # 12:00–21:00 UTC (owns London/NY overlap)
    return "ASIA"                                # 22:00–07:00 UTC


def simulate(high, low, close, e, s, start, is_long):
    """R from a fill at price e on bar `start` (SL dist s, TP 2.5R, ≤MAX_HOLD bars)."""
    sl = e - s if is_long else e + s
    tp = e + TP_R * s if is_long else e - TP_R * s
    end = min(start + MAX_HOLD, len(close) - 1)
    for j in range(start + 1, end + 1):
        if is_long:
            if low[j] <= sl:
                return -1.0
            if high[j] >= tp:
                return TP_R
        else:
            if high[j] >= sl:
                return -1.0
            if low[j] <= tp:
                return TP_R
    last = close[end]
    return (last - e) / s if is_long else (e - last) / s


def run_pair(inst: str, wfill: int):
    df = load_tf(inst, "1h")
    h, l, c = (df[x].values for x in ("high", "low", "close"))
    hours = df["datetime"].dt.hour.values
    s_arr = atr(df, 14).values
    r = rsi(df["close"], 14).values
    k = stoch_k(df).values
    wr = williams_r(df).values
    ku, kl = keltner(df)
    ku, kl = ku.values, kl.values

    oversold = (r < 35) | (k < 20) | (wr < -80) | (c < kl)
    overbought = (r > 65) | (k > 80) | (wr > -20) | (c > ku)

    def trans(mask):                              # fire only on entry INTO the extreme
        out = mask.copy()
        out[1:] = mask[1:] & ~mask[:-1]
        out[0] = False
        return out

    n = len(c)
    pokes = {ses: [] for ses in SESSIONS}         # Study A: max outward poke / s
    # Study B: sweep[ses][f] = list of R (filled only); n_setup[ses] = setups seen
    sweep = {ses: {f: [] for f in FRACS} for ses in SESSIONS}
    n_setup = {ses: 0 for ses in SESSIONS}

    for setup_mask, is_long in ((trans(oversold), True), (trans(overbought), False)):
        for i in np.where(setup_mask)[0]:
            s = s_arr[i]
            if not np.isfinite(s) or s <= 0 or i + 1 >= n:
                continue
            ses = session_of(int(hours[i]))
            n_setup[ses] += 1
            j_end = min(i + 1 + wfill, n)
            if is_long:
                poke = (c[i] - l[i + 1:j_end].min()) / s
            else:
                poke = (h[i + 1:j_end].max() - c[i]) / s
            pokes[ses].append(max(poke, 0.0))
            for f in FRACS:
                if poke < f:
                    continue                      # limit never reached
                limit = c[i] - f * s if is_long else c[i] + f * s
                fill = next(j for j in range(i + 1, j_end)
                            if (l[j] <= limit if is_long else h[j] >= limit))
                sweep[ses][f].append(simulate(h, l, c, limit, s, fill, is_long))
    return pokes, sweep, n_setup


def merge(dst, src):
    for ses in SESSIONS:
        dst[0][ses].extend(src[0][ses])
        for f in FRACS:
            dst[1][ses][f].extend(src[1][ses][f])
        dst[2][ses] += src[2][ses]


def fmt_pokes(pokes, title):
    out = [f"\n── {title}: outward poke beyond signal close (×ATR, within W_FILL bars)",
           f"{'session':<9}{'n':>7}{'q50':>7}{'q75':>7}{'q90':>7}  P(poke≥f) f=0.33/0.5/0.7/0.9/1.0"]
    for ses in SESSIONS:
        p = np.array(pokes[ses])
        if len(p) == 0:
            continue
        probs = "/".join(f"{(p >= f).mean():.0%}" for f in FRACS)
        out.append(f"{ses:<9}{len(p):>7}{np.quantile(p, .5):>7.2f}"
                   f"{np.quantile(p, .75):>7.2f}{np.quantile(p, .9):>7.2f}  {probs}")
    return "\n".join(out)


def fmt_sweep(sweep, n_setup, title):
    out = [f"\n── {title}: offset sweep — expectancy per SETUP (missed = 0R)",
           f"{'session':<9}{'f':>6}{'n_fill':>8}{'fill%':>7}{'win%':>7}{'avgR':>8}{'PF':>7}{'E/setup':>9}"]
    for ses in SESSIONS:
        best = None
        for f in FRACS:
            rs = np.array(sweep[ses][f], dtype=float)
            ns = n_setup[ses]
            if ns == 0:
                continue
            nf = len(rs)
            if nf == 0:
                out.append(f"{ses:<9}{f:>6.2f}{0:>8}{0:>6.0f}%{'—':>7}{'—':>8}{'—':>7}{0:>9.4f}")
                continue
            win = (rs > 0).mean() * 100
            losses = rs[rs < 0].sum()
            pf = rs[rs > 0].sum() / abs(losses) if losses < 0 else float("inf")
            eps = rs.sum() / ns
            if best is None or eps > best[1]:
                best = (f, eps)
            pf_s = "inf" if pf == float("inf") else f"{pf:.2f}"
            out.append(f"{ses:<9}{f:>6.2f}{nf:>8}{nf/ns*100:>6.0f}%{win:>6.1f}%"
                       f"{rs.mean():>+8.3f}{pf_s:>7}{eps:>+9.4f}")
        if best:
            out.append(f"{'':9}→ best f = {best[0]:.2f}  (E/setup {best[1]:+.4f})")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wfill", type=int, default=W_FILL)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    fx_pool = ({s: [] for s in SESSIONS},
               {s: {f: [] for f in FRACS} for s in SESSIONS},
               {s: 0 for s in SESSIONS})
    xau = None
    for inst in REGISTERED:
        res = run_pair(inst, args.wfill)
        print(f"  [{inst}] setups: " + " ".join(f"{s}={res[2][s]}" for s in SESSIONS))
        if inst == "xauusd":
            xau = res
        else:
            merge(fx_pool, res)

    blocks = []
    blocks.append(fmt_pokes(fx_pool[0], f"FX pooled (10 pairs, wfill={args.wfill})"))
    blocks.append(fmt_sweep(fx_pool[1], fx_pool[2], "FX pooled"))
    if xau:
        blocks.append(fmt_pokes(xau[0], "XAUUSD (continuation instrument — fade sim, read with suspicion)"))
        blocks.append(fmt_sweep(xau[1], xau[2], "XAUUSD"))
    report = "\n".join(blocks)
    print(report)

    if args.out:
        p = ROOT / args.out
        p.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Offset-by-Session Study\n\n"
            "Does the optimal outward-offset width depend on the signal bar's session?\n"
            "H1 oscillator-extreme fade setups 2020–2026, limit at f×ATR outward, fill within "
            f"{args.wfill} bars, SL 1×ATR, TP 3.0R (v3). f = offset as a fraction of the stop.\n"
            "Sessions (UTC): ASIA 22:00–07:00, LONDON 07:00–12:00, NY 12:00–21:00 (owns 12–16 overlap).\n"
            "`E/setup` = total R / setups (missed fill = 0R) — the metric the offset trades off.\n\n"
            "**ADOPTED v3 (D034, 2026-07-04):** offset = session_mult × SL, EC-independent. "
            "Session read at ORDER PLACEMENT (UTC): **Asia 0.40 / London 0.20 / NY 0.30**. "
            "FX-pooled evidence — London/NY optimal ~0.20× SL (tight), Asia ~0.40–0.50 (wide); "
            "NY was worst at 0.50. Gold (continuation) inverts — wants a wide Asia offset (own row TBD).\n"
        )
        p.write_text(header + "\n```" + report + "\n```\n")
        print(f"\n✅ wrote {p}")


if __name__ == "__main__":
    main()
