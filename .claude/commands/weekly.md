---
description: Weekly Trading Zone forecast for one instrument (swing-agent, MCP-only)
argument-hint: [instrument]
---

Run the swing-agent Weekly Routine for **$ARGUMENTS** (one instrument; if omitted, ask which of
the 11: xauusd, eurusd, gbpusd, eurgbp, audusd, nzdusd, usdcad, usdchf, usdjpy, eurjpy, gbpjpy).

This repo is self-contained — do not read/write the parent `swing-trading` repo. MCP is the only
gateway to Postgres. Full contract: `ROUTINES.md`. Formulas: `CLAUDE.md` Core Formulas (v3).

> **Running "all instruments"?** Do NOT run 11 in one context — that trips session limits and
> long single runs drop the final `write_doc`. Fan out **one subagent per instrument** in **batches
> of ≤3 concurrent**; let each batch fully commit (Step 6 verify passes) before starting the next.
> Each subagent runs Steps 0–6 below for its instrument and returns a compact write-confirmation.

## Steps

0. **Idempotency preflight** — before anything, check what already landed for this week (retries
   and resumed runs are common):
   `sql_query("SELECT zone_id, status FROM zone_ledger WHERE week='{YYYY-WNN}' AND instrument='{instrument}'")`
   and confirm whether `forecast_doc` key `{YYYY-WNN}/{instrument}` exists (`list_docs` / `get_doc`).
   - Zones already `OPEN` → do **not** publish new/duplicate zones. Resume at whatever is missing
     (usually just Step 5's `write_doc`, or Step 4's `snapshot_features`).
   - Nothing exists → fresh run.
   - Never publish a second set of zones for a week that already has them — that is the main source
     of conflicting data.

1. **Read rules context via MCP** (words, not numbers — docs live in Postgres, not wiki/*.md):
   - `get_context_pack(instrument)` — constitution, setup_library, currency_exposure, this
     instrument's profile + confluence_criteria (R1 rubric), plus current macro (yield_environment)
     and calibration snapshots. This is your full judgment context.
   - **Token-cap fallback:** `get_context_pack` output can exceed the tool token cap. If it does, it
     is saved to a file — read the instrument's `confluence` rubric (and any other section you need)
     from that saved tool-result file, or pull the piece via `get_doc(doc_type, key)`
     (e.g. `get_doc("rulebook","{instrument}/confluence")`). No data is lost; do not skip the rubric.

2. **Pull DB-native context via MCP** — call, in this order:
   - `get_zone_context(instrument)` — structure/momentum/macro/ATR+SL/COT, DB-native. **Keep this
     exact dict** — Step 4 freezes it as the R1 feature snapshot.
   - `get_brief(instrument, kind="weekly")` — OHLC freshness, open zones, recent trades/verdicts
   - `run_replay(instrument=instrument)` — resolve prior week (retrospective HELD/BROKE/UNTESTED)
   - `get_calibration(instrument)` — edge performance gate
   - `get_news(instrument)` + `get_econ(["--instrument", instrument])` — headline/data-release context
   - Gates **before scoring** — call each `run_gate` with the instrument arg:
     - `run_gate("cb_calendar", ["--instrument", instrument])`
     - `run_gate("econ_calendar", ["--instrument", instrument])` (**requires `--instrument`** —
       without it the gate errors returncode 2; returncode 1 = advisory no-trade windows, not a block)
     - `run_gate("intervention_watch", ["--instrument", instrument])` — **JPY pairs only, MANDATORY**
       (usdjpy, eurjpy, gbpjpy); MoF spot-vs-level jawboning/intervention risk
   - Honor any hard block per the constitution (e.g. an RBNZ/CB decision inside the entry window).
   - **Coverage note:** the econ calendar may end before the 10-day window closes — treat a late-week
     "no events" as unverified; a /validate refetch confirms it.

3. **Decide** — score candidate Trading Zones with Zone Confluence (R1, max 10, floor 5.0) per the
   confluence rubric. Publish ≤3 zones (≤1 counter-trend). Do not force a counter zone to fill a slot.
   - **Contradiction Protocol** (avoid conflicting judgment): when macro bias conflicts with technical
     structure, add a `> [!warning]` Conflict callout in the prose, cap conviction **MEDIUM** regardless
     of R1, and record why in the doc body. A same-direction D1/H4 divergence (fade the bounce) is a
     *confluence*, not a conflict — do not mislabel it.

4. **Structured write FIRST** — this is the durable record even if the prose step fails. For every
   published zone, in this order, and **confirm each call returns success before the next**:
   1. `publish_zone(...)`
   2. `snapshot_features(zone_id, instrument, event_type="publish", features=<the get_zone_context
      dict from Step 2>)` — freezes the exact R1 feature vector the zone was scored on.

5. **Write the forecast prose LAST** (the largest write — most likely to drop on a flaky connection):
   - `write_doc(doc_type="forecast", key="{YYYY-WNN}/{instrument}", body=<full markdown>,
     instrument=instrument, week="{YYYY-WNN}", generated="{today}", title=..., frontmatter={...})`.
   - The prose numbers (direction, ranges, R1, conviction, invalidation, TP anchor) **must reconcile
     1:1 with the published `zone_ledger` rows** — never let the doc describe zones that differ from
     what was published. Keep the body complete but not bloated.
   - Rewrite the macro baseline **only if it moved materially**:
     `write_doc(doc_type="context", key="yield_environment", kind="macro", body=<updated markdown>)`.
     In an all-instruments run the first instrument sets it for the week; the rest leave it unless
     their read genuinely contradicts it.
   - Never write a derived number anywhere it could go stale — recompute from MCP each time.

6. **Verify & reconcile** — confirm both halves landed and agree:
   `sql_query("SELECT zone_id, status FROM zone_ledger WHERE week='{YYYY-WNN}' AND instrument='{instrument}'")`
   and confirm `forecast_doc` key `{YYYY-WNN}/{instrument}` exists. A zone with no matching doc, or a
   doc with no matching zones, is a broken half-run — finish the missing write.

## Retry rule (idempotent — never mutate to force a pass)

Writes are upserts keyed by natural key: same `zone_id`, same `doc_key`. If any write drops or fails
(connection closed mid-response, timeout), **retry the exact same call with the same key** until it
confirms. Do **not** change zone numbers, doc key, or body just to make a retry succeed — that
creates conflicting/duplicate records. `write_doc` versions any prior body into `doc_history`, so a
same-key rewrite is safe.
