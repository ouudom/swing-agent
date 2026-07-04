# swing-agent — Thin Application Migration Plan

**Goal:** compact the current markdown-authoring + SQLite research system into a self-hosted,
Dockerized application that runs unattended on a home server. Deterministic pipeline in code,
Postgres as the store, scheduled TwelveData polling, and the *judgment* leg (weekly forecast +
hourly validation) driven by **Claude Code on a schedule/routine** (local laptop or Anthropic-hosted
cloud routine) talking to the app through a **single MCP server** — no Agent SDK worker to build or
maintain.

> Status: IMPLEMENTING (2026-07-04, rev MCP). Phase 0 local parity is complete through live
> Postgres backfill/diff; Phase 1 pipeline bridge is running under Docker. The existing `scripts/`
> + parent `wiki/` tree stays the source of truth until the app reaches parity, then the app imports
> the deterministic scripts rather than forking them.
>
> **Architecture decision (locked):**
> - **One compact repo `swing-agent/`, exactly two folders: `wiki/` + `src/`.** `wiki/` is the AI's
>   **execution context + thinking pattern** — curated rules, per-instrument confluence + profile,
>   current macro/calibration state, output templates, **and exactly two AI-output folders:
>   `wiki/weekly-forecasts/` + `wiki/validations/`**. `src/` is the app. **`wiki/` holds ONLY
>   execution-context md** — nothing else: no `_HOT.md`, no `_INDEX.md`, no `decisions.md`, no
>   `research/`, no parent-repo history dump.
> - **AI leg = Claude Code on a schedule, not an Agent SDK worker.** It reads context from `wiki/`
>   (rules + its own prior weekly forecasts / validations) and writes new output to
>   `wiki/weekly-forecasts/` + `wiki/validations/` with native file tools + git; it gets numbers +
>   compute from an **MCP server** in `src`.
> - **`live` branch is the shared read/write branch** for both the manual `/weekly` command and the
>   hourly `/validate` routine. Path ownership (below) means their writes never collide.
> - **Deployment runs `src/` + Postgres only** — the container never reads a `.md`. `wiki/` (curated
>   execution context + AI output) is repo content for the AI leg's checkout, not baked into the image.

---

## 1. Design principle — split by determinism

The system already has a clean seam, proven by the `swing-fetch` subagent: **deterministic legs
run as code; only judgment needs an LLM.**

| Layer | Current scripts | Target | Notes |
|---|---|---|---|
| **Data ingest** | `fetch.py`, `weekly_pull.py` (orchestrator), `lib/ohlc_store.py`, `db.py` | **App service** | Cron-driven. Swap SQLite→Postgres at the `db.py` layer only. |
| **Indicators / structure** | `compute.py`, `structure.py` | **App service** | Pure math on OHLC. No network, no judgment. |
| **Gates (hard, deterministic)** | `check_cb_calendar.py`, `check_econ_calendar.py`, `check_intervention_watch.py`, `check_v1b.py`, `check_structured_news_event.py` | **App service** | Rules in → bool out. Run *before* the AI leg; AI can never override a hard block. |
| **EC scorer (deterministic approx)** | `entry_confluence.py` + `config/ec_spec.py` | **App service** | Fidelity-gated: it approximates each pair's R2 prose. Runs standalone. |
| **Replay / evaluation** | `zone_ledger.py`, `zone_outcomes.py`, `trade_outcome.py`, `calibration.py` | **App service (nightly batch)** | Reads OHLC + ledger, writes outcome tables + `calibration.md`. |
| **Exposure / netting** | `fx_exposure.py` | **App service** | Advisory ledger. |
| **News feed** | `check_news.py` (+ RSS pull in `weekly_pull.fetch_news`) | **App service** | Key-free RSS. |
| **JUDGMENT — stays LLM** | `/weekly` 5-section analysis · zone selection + R1 scoring · `/validate` bias-flip / re-forecast / narrative · macro synthesis (`yield_environment.md`) · Step 2b retrospective | **Claude Code routine** | Reads rules from the git repo (native), pulls numbers from MCP `get_brief`/`sql_query`, writes forecast/validation md to the repo (native + `git commit`), pushes the structured zone/verdict to the DB via MCP. |

**Rule of thumb:** if the output is a number or a bool, it is code. If the output is a *decision
under ambiguity* (which zones to publish, is the macro bias flipping, does this structure override
the confluence score), it is the AI leg.

**Why the AI leg stays on validate (not fully mechanical).** The deterministic pipeline *can* emit
✅ ORDER LIMIT / ❌ NO TRADE end-to-end — `trade_outcome.py` proves it by replaying the whole thing
with zero AI calls. But that replay is a *backtest approximation*, good enough to score history, not
equal to live judgment on four things: **bias-flip read** (macro/yield/DXY/news synthesis vs. static
gate thresholds), **re-forecast trigger** (the "is this regime change" half isn't codified),
**EC fidelity gap** (`ec_spec.py` is a flagged approximation of the richer `confluence_criteria.md`
prose), and **conviction/narrative** (the auditable reasoning the mechanical path produces none of).
So validate runs as an **AI review layer over a mechanical brief**: the app computes SL/offset/TP/
EC/gates/limit price; the AI confirms-or-overrides the bias-flip / re-forecast call and writes the
narrative. Cheaper than "AI derives everything" (it reads a pre-computed brief), but keeps judgment
live instead of frozen into `ec_spec.py`.

---

## 2. Architecture — one compact repo, two folders (`wiki/` + `src/`); deploy runs `src/`

Everything is one repo, `swing-agent/`, with exactly two folders. `wiki/` is the AI's execution
context + thinking pattern (curated rules + templates + its own prior weekly forecasts/validations).
`src/` is the deployed app
(pipeline + MCP server over Postgres — no markdown, no file mounts). Claude Code reads/writes `wiki/`
natively and commits on the `live` branch; the deployed container builds `src/` only. The AI leg is
**Claude Code, external** — the manual `/weekly` command and the hourly `/validate` routine — getting
context from its `wiki/` checkout and numbers + compute from the MCP server. No Agent SDK worker.

```
swing-agent/                         ← ONE repo · `live` branch = command + routine read/write
  wiki/                             ← AI EXECUTION CONTEXT ONLY (curated, no parent-wiki copy)
    system/constitution.md                    ← risk / SL·TP·offset / gates / zone rules
    system/calibration.md                     ← current edge (which pairs working/dead)
    system/setup_library.md                   ← recurring zone patterns (thinking pattern)
    system/currency_exposure.md               ← FX netting (validate-time)
    system/yield_environment.md               ← macro baseline (weekly rewrites)
    system/{instrument}/{confluence_criteria, *_profile}.md
    templates/{weekly_forecast, daily_validation}.md
    weekly-forecasts/{YYYYWNN}/{instrument}.md ← /weekly output; AI reads back as context
    validations/{YYYYMM}/{YYYYMMDD}/{instrument}.md ← /validate output; AI reads back as context
  src/                              ← THE DEPLOYED APP (all the container builds)
    docker-compose.yml
    .env                            # TWELVE_DATA_KEY, FRED_KEY, TELEGRAM_*, DB creds, MCP_AUTH_TOKEN
    database/  init.sql             ← ALL numbers, source of truth
    pipeline/  scheduler.py, tasks/ ← fetch, compute, gates, EC, replay, calibration, brief
    mcp-server/ server.py           ← data + compute + structured-write tools (§5)
    engine/                         ← deterministic scripts imported by pipeline + mcp-server
```

```
┌── DEPLOYED: src/ + postgres (home server / VPS) ──────────────────┐
│  ┌── postgres ─────────────────────────────────┐                  │
│  │ ohlc · macro · market · news · econ_cal      │                  │
│  │ zone_ledger · zone_outcome · trade_outcome   │                  │
│  └──────────────────────────────────────────────┘                  │
│        ▲ write            ▲ read/write                             │
│  ┌── pipeline (cron) ─────┴──┐   ┌── mcp-server ──────────────────┐│
│  │ fetch→compute→gates→EC    │   │ DATA:    get_brief, sql_query, ││
│  │ mechanical order-brief    │──▶│          run_gate, get_news…   ││
│  │ nightly replay+calibration│DB │ COMPUTE: run_backtest,         ││
│  └───────────────────────────┘   │          run_replay, run_calib,││
│                                   │          compute_indicators    ││
│                                   │ WRITE:   publish_zone,         ││
│                                   │          write_verdict → DB    ││
│                                   └───────────────┬────────────────┘│
└───────────────────────────────────────────────────┼────────────────┘
                                                     │ MCP (authenticated)
                    ┌────────────────────────────────┴───────────────┐
                    │ Claude Code (EXTERNAL) on the `live` branch     │
                    │ context ↔ wiki/ checkout (native Read/Write+git)│
                    │   reads wiki context+prior output · writes output│
                    │ numbers+compute ↔ MCP:                          │
                    │   get_brief, sql_query, run_backtest, publish_* │
                    │ /weekly (manual) · /validate (hourly routine)   │
                    │ + ad-hoc context / research · model opus-4-8    │
                    └─────────────────────────────────────────────────┘
```

**Why this is thin.** The deployed container builds `src/` only — it never reads a `.md`. All of
`wiki/` (curated execution context + AI output) is repo content for the AI leg's git checkout, not
baked into the image, so a weekly/validation push touches only `wiki/weekly-forecasts/` or
`wiki/validations/` and never triggers a `src/` redeploy. The DB holds every number; `wiki/` holds
every execution word; the running app touches only the DB.

**Consistency (prose in git, structured zone in DB).** A run writes to two places: the narrative md
(git) and the structured zone/verdict (DB via `publish_zone`/`write_verdict`). Order of operations:
**DB write first** (it's what generates orders), then md + `git commit`. `publish_zone` is idempotent
on `zone_id`, so a re-fired routine reconciles rather than duplicates; the md write is append/rewrite
per File Rules. The DB is authoritative for orders; the md is the human-readable mirror.

**Network exposure.** A **laptop/LAN** routine reaches the MCP server on the private network and has
the repo locally — no public exposure at all. A **cloud routine** needs (a) the MCP endpoint behind a
tunnel (Cloudflare Tunnel / Tailscale Funnel) with `MCP_AUTH_TOKEN`, and (b) `git clone/push` creds
for the repo — two connections, both authenticated. Postgres stays internal-only either way; the AI
leg only ever sees the MCP server, never the DB.

---

## 3. Data model — SQLite → Postgres

The store is already a clean 10-table SQLite DB (`data/database/index.db`). Migration is mechanical:

1. **Schema:** translate the SQLite `CREATE TABLE`s to Postgres in `database/init.sql`.
   Types: `REAL`→`double precision`, `TEXT` timestamps→`timestamptz` (store UTC, no tz math change),
   add explicit PKs (e.g. `ohlc (symbol, timeframe, datetime)`), index on `(symbol, timeframe,
   datetime)` and `zone_ledger(zone_id)`.
2. **`db.py` abstraction:** today it wraps SQLite. Point it at Postgres via SQLAlchemy or `psycopg`.
   Keep the same `read_table / write_table / sync_table` surface so *no caller changes*. This is the
   single most valuable refactor — every script talks to `db.py`, not to SQLite directly.
3. **One-time backfill:** `sqlite3 → pandas → to_sql(postgres)` per table. The existing hourly
   `db_guard.py` `VACUUM INTO` backups are the migration snapshot source.
4. **Bad-tick guard** (`ohlc_store.upsert` quarantine) ports unchanged — it is pure logic.

Keep `db_guard.py`-style backups on Postgres too (`pg_dump` nightly, keep 7).

---

## 3b. Storage — Postgres for numbers, `wiki/` for prose; `src/` deploy holds no markdown

**Split by home: tabular → Postgres (`src/database`). Execution prose → curated `wiki/` (rules +
templates + `wiki/weekly-forecasts/` + `wiki/validations/`), on the `live` branch.** Claude Code reads/writes `wiki/` with native file tools;
git is the audit trail. The **deployed `src/` container never reads a `.md`.**

The deterministic engine needs **zero markdown** — scripts read config (`config/*.py`, JSON
calendars) and OHLC, and write DB tables + the brief. `ec_spec.py` *approximates* the confluence
prose in Python; it never reads the `.md`. Backtests read OHLC from the DB + config. So `src/` runs
headless on **DB + config alone**. Markdown matters only to the AI leg and to you.

| Content | Home | Who touches it | Why |
|---|---|---|---|
| **Tabular** — ohlc, macro, market, news, econ, zone_ledger, zone_outcome, trade_outcome, gld_holdings | **Postgres** (`src/`) | pipeline writes; AI reads via MCP `sql_query`/`get_brief`; AI writes structured via `publish_zone`/`write_verdict` | Queryable, frontend + order-gen read it, source of truth for every number. |
| **Execution rules + thinking pattern** — curated `wiki/*` (constitution, per-instrument confluence + profile, macro, calibration, setup_library, currency_exposure, templates) | **repo, `live` branch** | you + Claude Code hand-edit (native `Edit`); `git diff` = audit | Only execution-context md. Not a copy of the parent `wiki/`. |
| **Weekly forecast prose** — `wiki/weekly-forecasts/{YYYYWNN}/{instrument}.md` | **repo, `live` branch** | Claude Code `/weekly` writes (native `Write`) + `git commit`; reads its own prior output back as context | AI-owned output trail, seeded from the parent repo's history at migration (§ copy-in below). Structured zones go to DB via `publish_zone`. |
| **Validation prose** — `wiki/validations/{YYYYMM}/{YYYYMMDD}/{instrument}.md` | **repo, `live` branch** | Claude Code `/validate` writes (native `Write`) + `git commit`; reads its own prior output back as context | AI-owned output trail, seeded from the parent repo's history at migration (§ copy-in below). Structured verdicts go to DB via `write_verdict`. |

**Compact — `wiki/` is EXECUTION CONTEXT ONLY.** Nothing that isn't used to run `/weekly` or
`/validate` lives here. Build it as a **curated skeleton**, not a copy of the parent repo's `wiki/`.
Allowed md only:
- `system/{constitution,calibration,setup_library,currency_exposure}.md`
- `system/yield_environment.md`
- `system/{instrument}/{confluence_criteria,*_profile}.md`
- `templates/{weekly_forecast,daily_validation}.md`
- `weekly-forecasts/{YYYYWNN}/{instrument}.md` written by swing-agent `/weekly` (e.g. `2026W27/xauusd.md`)
- `validations/{YYYYMM}/{YYYYMMDD}/{instrument}.md` written by swing-agent `/validate` (e.g. `20260704/xauusd.md`)

Excluded from `swing-agent/wiki/`:
- `_HOT.md`, `_INDEX.md` — boot/nav state. The app boots from DB + config, not a markdown state file.
  (Removing them also removes the *only* shared-mutable md — the reason the two-writer git story below
  is conflict-free.)
- `decisions.md` — the design belief log (*why* the system is built this way). Meta, not execution.
  **Migration guard:** before cutting it, verify every still-ACTIVE rule in `decisions.md` is already
  reflected in `constitution.md` / the confluence files — the belief log occasionally carries a live
  rule that hasn't been folded into the constitution yet.
- `research/*` — analysis history stays outside the deployed swing-agent repo.

**Historical forecasts/validations ARE copied in** (revised — was "do not bulk-import" in an earlier
draft of this plan). Source: parent repo's `forecasts/weekly/{instrument}/YYYY-WNN.md` and
`forecasts/daily/{instrument}/YYYY-MM-DD.md`. Transform on copy: old layout is
instrument-then-date; new layout is date-then-instrument — `forecasts/weekly/xauusd/2026-W27.md` →
`wiki/weekly-forecasts/2026W27/xauusd.md`, `forecasts/daily/xauusd/2026-06-08.md` →
`wiki/validations/202606/20260608/xauusd.md` (validations add a `YYYYMM` month-grouping level
above the day). Content copied verbatim (no rewrite); only the path changes.

**Can it all move to Postgres instead?** Technically yes (a `wiki` table, a `forecast` table). But
you'd lose `git diff`/blame on rule changes (the audit backbone) and Claude Code's native file I/O.
**DB is canonical for numbers; `wiki/` is canonical for prose.** No prose in the DB, no numbers in
the repo.

---

## 4. Scheduling

Cadence (confirm): **15 min during active hours, 30 min overnight, paused over the weekend.**

```
Fetch OHLC (TwelveData 15M bars):
  Mon 00:00 UTC → Fri 21:00 UTC
    07:00–21:00 UTC  → every 15 min   (London + NY active)
    21:00–07:00 UTC  → every 30 min   (Asia / overnight)
  Fri 21:00 → Sun 21:00 UTC → PAUSED (market closed; matches existing cache policy)

Derived (chained after each fetch): compute indicators → hard gates → EC score.

Pipeline batch jobs (deterministic, in-app cron):
  Nightly ~22:00 UTC → zone_outcomes → trade_outcome → calibration
  Friday  13:00 UTC  → cancel unfilled limits (weekend-gap policy, v3)
  Continuously       → refresh the mechanical brief (indicators/gates/EC/limit price) so the
                       AI leg always reads a current pre-computed brief when it fires.

AI-leg jobs (Claude Code routine → MCP; scheduled OUTSIDE the app):
  Weekly  Mon 06:00 UTC   → /weekly forecast (all 11 instruments) → write wiki/weekly-forecasts + publish_zone
  Hourly  :30 past, London→NY → /validate (all PENDING zones) → write wiki/validations + write_verdict
```

**Two schedulers, on purpose.** The pipeline's own APScheduler runs the deterministic legs (they
must run whether or not the AI leg ever fires). The AI leg is scheduled *separately* as a Claude Code
routine (laptop cron or Anthropic cloud routine) — decoupled so the mechanical order-brief stays
fresh even if the AI leg is paused, and so you can trigger a manual `/weekly` any time without
touching the pipeline. Hourly validate matches today's live cadence; the D032 4h anchor-lock already
prevents the hourly re-run from whipsawing a resting limit.

**Rate limit (critical):** TwelveData free tier = **8 credits/minute**. 11 pairs × ~1 credit each
blows the cap in one unpaced loop (this exact bug caused the OHLC freshness stagger — already fixed
with 9 s pacing in `fetch.py` / `weekly_pull.py`). In the app: either keep the ≥9 s inter-instrument
pacing, or move to a paid tier and parallelize. A 15-min poll of 11 pairs at 9 s spacing = ~100 s,
comfortably inside the window.

Scheduler options: **APScheduler inside the pipeline container** (simplest, one process, timezone
aware) or host `cron` calling `docker compose run`. Prefer APScheduler — keeps everything in one
service and survives restarts via a jobstore.

---

## 5. The AI leg — Claude Code routine; MCP = data + compute gateway

**No Agent SDK, no headless worker.** The AI leg is Claude Code running the `/weekly` and `/validate`
skills (plus ad-hoc research) on a schedule. **Prose comes from the git repo** (native file tools);
**numbers and compute come from the MCP server.** The MCP surface is deliberately broad — enough to
run weekly, run validate, answer context questions, and drive research/backtests — because those are
the same deterministic engine calls, and putting them behind MCP lets the routine do them local
**or** cloud without local script access.

### MCP tool surface (data + compute + structured writes — never prose)

*Context / data (read):*
- `get_brief(instrument, kind)` — the pre-computed weekly/validate brief: indicators, structure, gate
  results, EC score, and the mechanical SL/offset/TP/limit price. (The weekly-pull text builder,
  returned over MCP instead of written to a file.) Keeps tokens on judgment, not derivation.
- `sql_query(sql)` — read-only Postgres (ohlc, macro, market, news, econ, ledger, outcomes).
- `run_gate(name, args)` — CB / econ / intervention / V1b bool + reason.
- `get_news(instrument)` / `get_econ(window)` — convenience readouts (or via `sql_query`).
- `get_calibration(slice)` — current edge performance (win%/R by instrument/direction/R1/session).

*Compute / research (run the engine on demand):*
- `run_backtest(name, args)` — run a backtest script (`backtest_offset_session`, `backtest_e0_variants`,
  `backtest_signals`, …) and return the result table. This is exactly the 45k-event offset study run
  this session — the routine can now do that research over MCP and write the `.md` writeup to git.
- `run_replay(week?, instrument?)` — `zone_outcomes` / `trade_outcome` replay on demand → returns R,
  fill, gate-accuracy rows.
- `run_calibration()` — regenerate the calibration aggregates (returns the summary; the routine writes
  `calibration.md` to git).
- `compute_indicators(instrument, tf)` — ad-hoc "what does EC/ADX/structure look like right now" for
  a context question, without a full brief.

*Structured writes (the order/verdict path — DB only):*
- `publish_zone(zone_id, ...)` — register a published zone → `zone_ledger` (idempotent on `zone_id`).
- `write_verdict(zone_id, verdict, ec, limit_price, ...)` — validate verdict/override → `zone_ledger`.

*(Web search: use Claude Code's own built-in — no MCP proxy. Prose read/write: native git file tools
in the repo — no `read_wiki`, `publish_forecast`, or `write_validation` MCP tools.)*

### How each run works

- **Weekly** (`/weekly`, Mon): read the pair's rules + last swing-agent forecast from `wiki/` → `get_brief` +
  `sql_query`/`run_backtest` as needed → apply zone-selection + R1 judgment → `git`-write
  `wiki/weekly-forecasts/{week}/{inst}.md` → `publish_zone` for each published zone.
- **Hourly validate** (`/validate`): read rules + this week's forecast from `wiki/` → `get_brief`
  (carries the mechanical verdict + limit price) + own web search for news/macro → confirm-or-override
  the bias-flip / re-forecast call → `git`-write `wiki/validations/{month}/{date}/{inst}.md` →
  `write_verdict`.
- **Ad-hoc context / research** (you ask): `get_brief` / `sql_query` / `run_backtest` / `run_replay`
  → analysis returned to you. swing-agent stays compact (no `research/` folder); persist any writeup
  outside the deployed swing-agent repo if you want it kept. This is the "deep review / backtest offset+EC"
  workflow from this session — the numbers now come over MCP instead of local scripts.

### Guardrails (non-negotiable)

1. **Gates run in code first.** Hard blocks (CB day, MoF, V1b breach, event window) are enforced in
   the brief *before* the AI sees it; `get_brief` reports a hard-blocked zone as blocked. Enforce it
   again server-side: `publish_zone`/`write_verdict` **reject** a verdict that contradicts a hard gate.
2. **Mechanical numbers are computed by code** and handed over as facts. The AI decides *whether to
   publish* and *how to frame* — it never invents SL/offset/TP/EC/limit price.
3. **Audit trail:** the MCP server logs every `get_brief` alongside the `publish_zone`/`write_verdict`
   it accepts; `trade_outcome.py` can later verify the AI honored every gate. Divergence = bug.
4. **DB idempotency + git for the rest:** `publish_zone`/`write_verdict` are idempotent on `zone_id`,
   so a re-fired routine reconciles. Forecast immutability (no overwrite of a post-Monday weekly file)
   is enforced by the File Rules on the git side — Claude Code already honors them.

---

## 5b. Git workflow — the `live` branch

Both the manual `/weekly` command and the hourly `/validate` routine read and write prose on **one
long-lived branch, `live`**. This works without merge conflicts because of **path ownership** — the
two writers never touch the same file.

**Branch model:**
- **`live`** — the working branch for command + routine. All forecast churn (24 daily commits/day
  from validate + weekly commits) lives here.
- **`main`** — your dev + rule edits. When you change rules (constitution / confluence / profile),
  merge `main → live` so the routine reads the latest rules. `live` = `main` + forecast churn.
- (`live` tracks `main`; it is not an orphan branch — a run needs rules *and* writes forecasts in the
  same working tree, so both must be present on the one branch it checks out.)

**Path ownership — the rule that makes it conflict-free:**

| Writer | Owns (writes only) | Reads |
|---|---|---|
| `/weekly` (manual, laptop) | `wiki/weekly-forecasts/{week}/{inst}.md`, `wiki/system/yield_environment.md` | `wiki/*` rules, last swing-agent forecast |
| `/validate` (hourly routine) | `wiki/validations/{month}/{date}/{inst}.md` — **nothing else** | `wiki/*` rules, this week's weekly forecast, `get_brief` |

Weekly and daily forecast paths never overlap (different top-level dirs). Within one
`weekly-forecasts/{week}/` folder, each instrument's `/weekly` run writes a distinct `{inst}.md`
filename, so concurrent runs share a folder without touching the same blob — still conflict-free.
`yield_environment`
is weekly-only-write / validate-read. **There is no file both legs write** — so no content conflict is
possible, even on the same branch. (This is why dropping `_HOT`/`_INDEX` mattered: they were the only
shared-mutable md.)

**Per-run discipline (every command + routine run):**
```
git checkout live && git pull --rebase        # get the other writer's latest
… read curated wiki context + prior swing-agent output, do judgment …
write_verdict / publish_zone   → DB via MCP    # DB FIRST — authoritative for the order
write wiki/weekly-forecasts/{...}.md or wiki/validations/{...}.md  → native Write
git add wiki/weekly-forecasts/… wiki/validations/… && git commit && git push
```

Because validate only *adds* new validation files, its pushes are clean fast-forwards ~always. DB-first
means a failed push leaves the order correct in the DB; the md re-syncs on the next run. A nightly
reconcile can flag any `zone_ledger` row with no matching weekly/validation output file (or vice versa).

---

## 6. Migration phases

### Phase 0 — Repo skeleton + Postgres behind `db.py` (local parity)

**Goal:** create the compact `swing-agent/` shape, then change storage only. Deployment root is
`swing-agent/`; deterministic engine scripts are vendored under `src/engine/scripts/`.

**0.0 Curated `wiki/` skeleton — DONE 2026-07-04**
- Create only `swing-agent/wiki/` + `swing-agent/src/`.
- Under `wiki/`, create only allowed execution-context paths from §3b:
  `system/`, `templates/`, `weekly-forecasts/`, `validations/`.
- Do **not** copy the parent repo's `wiki/` wholesale.
- Do **not** copy historical parent `forecasts/weekly` or `forecasts/daily`.
- Seed rules by curated extraction only: active execution rules into `system/*`, templates into
  `templates/*`; first swing-agent run creates the first weekly forecast / validation output.

**0.1 Schema inventory — DONE 2026-07-04**
- Dump current SQLite schema + row counts for every table.
- Decide explicit Postgres PKs and indexes before writing `init.sql`.
- Map timestamp columns to UTC `timestamptz`; keep instrument/timeframe text values unchanged.

**0.2 Postgres bootstrap — DONE 2026-07-04**
- Add `src/docker-compose.yml` with Postgres only.
- Add `src/database/init.sql`.
- Add `.env.example`; keep real `.env` local only.
- Add `pg_dump` backup command equivalent to current `db_guard.py` retention policy.

**0.3 `db.py` adapter — DONE 2026-07-04 (SQLite-smoked; Postgres runtime validation in 0.4)**
- Refactor `scripts/db.py` behind a backend switch (`sqlite` default, `postgres` opt-in).
- Preserve `read_table / write_table / sync_table / read_ohlc / read_slice / sync_slice` call shape.
- Add transaction boundaries around multi-table writes.

**0.4 Backfill + diff harness — DONE 2026-07-04**
- Export latest SQLite backup into Postgres.
- Compare table row counts, min/max datetimes, and sample hashes by table.
- Run representative scripts against both backends and diff outputs:
  `weekly_pull.py`, `zone_ledger.py list`, `zone_outcomes.py`, `trade_outcome.py`,
  `calibration.py`, `fx_exposure.py`.
- Live Docker validation:
  - `docker compose up -d --build` passes; Postgres healthy, pipeline running.
  - Backfill inserted 1,007,223 valid OHLC rows plus all non-OHLC tables; skipped one all-blank
    legacy OHLC artifact row from SQLite.
  - SQLite/Postgres diff passes on counts, key ranges, and normalized sample hashes for all 10
    tables.

**Exit:** all current scripts pass against Postgres with identical output or documented harmless
ordering/type differences. Rollback = switch backend to SQLite.

### Phase 1 — Dockerize deterministic pipeline

**Goal:** app service runs numbers unattended. No MCP. No AI. No repo prose reads.

**1.1 Move importable engine — DONE 2026-07-04**
- Vendor deterministic scripts/config into `src/engine/scripts/`.
- Create `src/engine/` wrappers against the vendored engine; preserve original public command behavior.
- Deployment no longer depends on the old base repo path.

**1.2 Scheduler skeleton — STARTED 2026-07-04**
- Add `src/pipeline/scheduler.py` with APScheduler.
- Add pipeline Docker service; compose bind-mounts the `swing-agent/` root only (`/app == swing-agent`).
- Jobs: fetch OHLC, compute indicators, hard gates, EC scoring, brief refresh, nightly replay,
  Friday unfilled-limit cancel.
- Preserve TwelveData 9 s pacing unless paid tier confirmed.

**1.3 Observability**
- Structured logs per instrument/job.
- `pipeline_run` table or equivalent job ledger: started, finished, status, error, rows touched.
- Healthcheck: DB reachable, latest OHLC freshness by instrument/timeframe, last successful brief.

**1.4 Week-long soak**
- Run side-by-side with current local scripts.
- Compare OHLC freshness, indicator snapshots, replay tables, calibration output daily.

**Exit:** OHLC + indicators + gates + EC + outcomes update on schedule for one full trading week,
with no freshness stagger and no manual intervention. Rollback = stop container; local scripts remain
primary.

### Phase 2 — MCP read + compute tools

**Goal:** Claude Code can read numbers and run deterministic research over MCP, but cannot write
orders yet.

**2.1 Server shell — DONE 2026-07-04**
- Add `src/mcp-server/server.py`, auth token, request logging, error model.
- Expose read-only DB pool. Keep Postgres internal-only.
- Implemented as a localhost-bound HTTP tool bridge using stdlib server + bearer token; no
  write-order tools exposed.

**2.2 Read tools — DONE 2026-07-04**
- `get_brief(instrument, kind)`
- `sql_query(sql)` read-only with statement allowlist / timeout / row cap.
- `run_gate(name, args)`
- `get_news(instrument)`, `get_econ(window)`, `get_calibration(slice)`

**2.3 Compute tools — DONE 2026-07-04**
- `compute_indicators(instrument, tf)`
- `run_replay(week?, instrument?)`
- `run_calibration()`
- `run_backtest(name, args)` allowlisted by script name and bounded runtime.
- Docker validation: `/health`, `/tools`, `sql_query`, `get_brief`, `compute_indicators`,
  `get_calibration`, `run_gate`, and `run_replay` pass against local Postgres.

**2.4 Manual parity test — DONE 2026-07-04**
- Hand-run `/validate` for one pair using MCP data.
- Run one known backtest (offset session or E0 variants) and compare published result table.
- Added `src/scripts/mcp_parity_check.py`.
- EURUSD parity passed:
  - MCP `get_brief` latest OHLC + zone/trade counts match local DB.
  - MCP `compute_indicators` matches local formula output.
  - MCP `run_gate(econ_calendar)` matches local script return code + stdout.
  - MCP `run_backtest(e0_variants)` and DB-backed `run_backtest(offset_session)` match local output.

**Exit — DONE 2026-07-04:** MCP `/validate` data path matches local `/validate` inputs for EURUSD;
known backtests reproduce. Rollback = Claude Code returns to local scripts.

### Phase 3 — MCP structured writes + hourly validate

**Goal:** hourly routine writes verdicts to DB and validation prose to git.

**3.1 Write tools — DONE 2026-07-04**
- `publish_zone(zone_id, ...)` idempotent on `zone_id`.
- `write_verdict(zone_id, verdict, ec, limit_price, ...)` idempotent by zone/date/run.
- Server rejects hard-gate contradictions.
- Added `validation_verdict`, `notification_event`, and `routine_checkpoint` tables.
- Added MCP write tools: `publish_zone`, `write_verdict`, `queue_notification`,
  `update_checkpoint`.
- `write_verdict(ORDER_LIMIT)` rejects hard blocks and EC < 5.0.

**3.2 Reconcile tools — DONE 2026-07-04**
- DB↔git checker: ledger rows without matching `wiki/weekly-forecasts/*` / `wiki/validations/*`, and output files without DB rows.
- Routine retry contract: DB write first, md commit second, reconcile if push fails.
- Added `src/scripts/reconcile_db_git.py`.
- Scheduler runs reconcile nightly; strict mode available for CI/routines.

**3.3 Laptop routine — CODE READY / EXTERNAL ACTIVATION**
- Schedule hourly `/validate` on laptop first.
- Validate owns only `wiki/validations/{month}/{date}/{inst}.md`.
- Run manual shadow compare for several sessions before trusting live order path.
- Added `ROUTINES.md` with DB-first/git-second contract, laptop validate route, weekly route,
  cloud dry-run, and rollback.

**Exit:** app-side write/reconcile contract is implemented. Actual hourly Claude Code routine still
requires external scheduler/git credentials; rollback = disable routine; keep MCP writes available
for manual runs only.

### Phase 4 — Weekly routine + notifications

**Goal:** full week cycle runs hands-off from laptop routine.

**4.1 Weekly route — CONTRACT READY / EXTERNAL ACTIVATION**
- Schedule Monday `/weekly` for all 11 instruments.
- Weekly owns only `wiki/weekly-forecasts/{week}/{inst}.md` and `yield_environment.md`.
- Register every published zone through `publish_zone`.
- Weekly DB path is implemented via `publish_zone`; Claude Code routine activation remains external.

**4.2 Notifications — DONE 2026-07-04**
- Telegram for ORDER LIMIT, hard block, invalidation, weekly publish summary, routine failure.
- Include `zone_id`, instrument, verdict, reason, and link/commit hash where useful.
- MCP write tools queue `notification_event`; `send_notifications.py` sends pending Telegram events
  when Telegram env exists. Scheduler runs it every 5 minutes. `--dry-run` available.

**4.3 Full-cycle soak — PENDING LIVE WEEK**
- Run weekly publish → hourly validates → Friday cancel → nightly replay for one full week.
- Compare manual spot checks against current command behavior.

**Exit:** full weekly→hourly→Friday→replay cycle runs hands-off. Rollback = manual `/weekly` +
manual/laptop `/validate`.

### Phase 5 — Cloud routine (optional) + retire manual path

**Goal:** move scheduling off laptop only after local parity is boring.

**5.1 Secure exposure — RUNBOOK READY**
- Expose MCP via Cloudflare Tunnel or Tailscale Funnel.
- Require `MCP_AUTH_TOKEN`; keep Postgres private.
- Give routine git clone/push credentials limited to the repo.
- Covered in `ROUTINES.md` + Ubuntu deployment guide. No public exposure enabled locally.

**5.2 Cloud dry run — PENDING CREDENTIALS**
- Run cloud routine in shadow mode first: read MCP, write md to test branch, no DB writes.
- Then enable DB writes for one instrument; expand only after reconcile stays clean.

**5.3 Cutover — PENDING SOAK**
- After ~4 stable weeks, app becomes primary.
- Parent `scripts/` becomes imported engine / compatibility path, not operational source.

**Exit:** cloud routine matches laptop routine and reconcile remains clean. Rollback = laptop routine.

---

## 7. Open questions / risks

- **AI cost + latency** per weekly run (11 instruments × 5-section analysis). Budget it (`effort`
  sweep, `task_budget`); consider fanning instruments across parallel routine steps.
- **Non-determinism** in the judgment leg — the audit trail (guardrail 3) is how we keep it honest.
- **Prose/DB consistency** — a run writes narrative (git) and structured zone (DB via MCP). DB-first
  ordering + `zone_id` idempotency keep them reconcilable, but a routine that dies between the two
  leaves the md without a ledger row (or vice versa). The DB is authoritative for orders; a nightly
  check can flag zones in `zone_ledger` with no matching forecast file (and vice versa).
- **Cloud routine = two authenticated connections** — MCP (tunnel + `MCP_AUTH_TOKEN`) *and* git
  (`clone/push` creds). Laptop routine has neither problem (repo local, MCP on LAN). Prefer laptop
  until the cadence genuinely needs off-laptop scheduling.
- **Econ-calendar upstream break** — ForexFactory `lastweek`/`nextweek` JSON currently 404; the
  websearch fallback must be wired before the app relies on scheduled econ data. (Carried open from
  the 2026-07 corrections batch.)
- **Secrets** — `.env` in the compose stack; do not bake keys into images. Keep Postgres
  internal-only, no public port; only the MCP server is ever exposed (and only via tunnel + token).
- **Gold (xauusd) offset** — the v3 session offset table is FX-tuned; gold (momentum) wants a wider
  Asia value. Flagged as a watch; may earn its own row before the app hard-codes the table.

---

## 8. What ports as-is vs needs rework

**Ports unchanged (pure logic):** `compute.py`, `structure.py`, `entry_confluence.py`,
`ec_spec.py`, all `check_*.py` gates, `zone_outcomes.py`, `trade_outcome.py`, `calibration.py`,
`fx_exposure.py`, the bad-tick quarantine.

**Needs rework:** `db.py` (SQLite→Postgres — the one real refactor), `fetch.py` /`weekly_pull.py`
(wrap in the scheduler; pacing already added). The `/weekly` + `/validate` skills **stay Claude Code
skills** — they read rules and write forecasts as **native repo files** (unchanged), and swap only
their *data* calls (running local scripts) for MCP tools (`get_brief`, `sql_query`, `run_gate`,
`run_backtest`, `publish_zone`, `write_verdict`). Judgment prose unchanged.

**New code:** `docker-compose.yml`, `database/init.sql`, `scheduler.py`, the **MCP server** (data +
compute + structured-write tools: `get_brief`, `sql_query`, `run_gate`, `get_news`/`get_econ`,
`get_calibration`, `run_backtest`, `run_replay`, `run_calibration`, `compute_indicators`,
`publish_zone`, `write_verdict` — with server-side gate enforcement + `zone_id` idempotency), and the
brief-assembler (mostly a rename of the existing weekly-pull text builder, now returned by
`get_brief`). **Not built:** any Agent SDK worker, any file-serving MCP tools (prose is git), any
`wiki/`/markdown mount in the app.
