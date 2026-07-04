"""Per-instrument config package. Modules: config.<instrument> (flat, one file per pair)."""


def price_dp(cfg) -> int:
    """Display/rounding precision for a pair. Explicit cfg.PRICE_DP wins; otherwise the
    legacy TICK heuristic: 2 dp for gold-scale (TICK<=100), 5 dp for FX-scale. Single
    source shared by fetch_data.load_instrument and zone_context (was duplicated)."""
    if hasattr(cfg, "PRICE_DP"):
        return int(cfg.PRICE_DP)
    return 2 if getattr(cfg, "TICK_MULTIPLIER", 100) <= 100 else 5
