#!/usr/bin/env python3
"""
Full rebuild of zone_outcome + zone_atr_sl_outcome from the current zone_ledger +
OHLC store. Wipes both tables (no merge with prior rows) before rewriting every
zone fresh — use after a rule change in zone_outcomes.py (fill model, SL source,
market-close handling) that breaks numeric comparability with previously
resolved rows. zone_ledger itself is not touched except for its `status` column,
which is recomputed from this run's zone_outcome results.

Usage:
    bash scripts/pyrun.sh scripts/replay/backfill_zone_outcomes.py
"""
from __future__ import annotations

from zone_outcomes import ATR_TABLE, OUTCOMES_TABLE, run_replay, summarize


def main():
    print(f"── wiping + rebuilding {OUTCOMES_TABLE} (SL = zone width; drives zone_ledger.status) " + "─" * 10)
    res_zone = run_replay(OUTCOMES_TABLE, "zone", update_ledger=True, wipe=True)
    summarize(res_zone)

    print(f"\n── wiping + rebuilding {ATR_TABLE} (SL = constitution ATR; comparison only) " + "─" * 10)
    res_atr = run_replay(ATR_TABLE, "atr", update_ledger=False, wipe=True)
    summarize(res_atr)


if __name__ == "__main__":
    main()
