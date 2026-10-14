# CLAUDE.md — Build Instructions for Claude Code

This file is the entry point for Claude Code. Read this first, then
`docs/ARCHITECTURE.md` and `docs/DATA_SOURCES.md` before writing any code.

## What this project is

A daily-run agent that forecasts GBP/INR over the next 30 days for a
personal use case (paying UK university fees / living expenses from
India). It pulls market + macro + news data, compiles it into a single
structured snapshot, sends that snapshot to the Claude API with a
forecasting prompt, and stores the structured JSON result (base / bull /
bear scenarios with probabilities) for tracking over time.

This is NOT a trading bot. No orders are placed. Output is informational
only and must say so.

## Build order (do these in sequence, commit after each)

1. **Scaffolding** — `requirements.txt`, `.env.example`, `config.py`
   (loads env vars, no secrets hardcoded).
2. **Collectors** (`src/collectors/`) — one file per data source, each
   returning a plain Python dict. See `docs/DATA_SOURCES.md` for exact
   sources, libraries, and the dict shape each collector must return.
3. **Compiler** (`src/compiler/build_snapshot.py`) — merges all collector
   outputs into one `snapshot.json` matching the schema in
   `docs/SNAPSHOT_SCHEMA.md`. Must run even if some collectors fail
   (degrade gracefully, mark missing fields as `null`, never crash the
   whole pipeline because one source is down).
4. **Forecaster** (`src/forecaster/run_forecast.py`) — loads
   `prompts/forecast_prompt.md`, fills in the snapshot, calls the Claude
   API (see `docs/CLAUDE_API_NOTES.md`), validates the response against
   `docs/FORECAST_SCHEMA.md`, retries once on invalid JSON.
5. **Storage** (`src/storage/`) — append each day's snapshot + forecast
   to `data/history.jsonl` (one JSON object per line). Also write the
   latest forecast to `output/latest_forecast.json` and a human-readable
   `output/latest_forecast.md`.
6. **Orchestrator** (`src/main.py`) — runs steps 2-5 in order, logs to
   stdout, exits non-zero only if the forecaster step itself fails (not
   if individual collectors fail).
7. **Delivery (optional, build last)** — `src/storage/notify.py`: email
   or Telegram push of `output/latest_forecast.md`. Read
   `docs/DELIVERY_OPTIONS.md` and ask the user which one they want before
   building this step.
8. **Scheduling** — fill in `.github/workflows/daily_forecast.yml` to run
   `src/main.py` on a daily cron and commit `data/history.jsonl` +
   `output/` back to the repo (or push to the chosen delivery channel).
9. **Tests** — at minimum, unit tests for the compiler (schema is
   respected) and a mocked test for the forecaster (no real API calls in
   CI).

## Hard constraints

- No API keys, secrets, or tokens ever hardcoded — everything from `.env`
  / GitHub Actions secrets, loaded via `config.py`.
- Every collector must work standalone (`python -m
  src.collectors.spot_rate`) and print its dict, for easy debugging.
- All dates/timestamps in UTC, ISO 8601.
- The forecaster must request and parse **strict JSON** from Claude — no
  markdown fences, no prose outside the JSON object. If parsing fails
  twice, log the raw response and exit non-zero rather than silently
  writing garbage.
- Money/rate numbers: always store as floats with 4 decimal places, never
  strings.
- Add a one-line disclaimer field (`"disclaimer"`) into every stored
  forecast: short-horizon FX forecasts are not reliable trading signals;
  this is for budgeting awareness only.

## Tech choices (use these unless there's a good reason not to)

- Python 3.11+
- `httpx` for HTTP calls (not `requests`, for async-readiness later)
- `pandas` + `pandas-ta` for technicals
- `yfinance` for FX history
- `python-dotenv` for local env loading
- `anthropic` official SDK for the Claude API call
- `pydantic` for schema validation (snapshot + forecast)

## What to ask the user before building

Claude Code should pause and ask the user (don't assume):
1. Which delivery method they want (email / Telegram / just a Sheet/repo
   file) — see `docs/DELIVERY_OPTIONS.md`.
2. Whether to run on GitHub Actions (free, requires pushing API key as a
   repo secret) or locally via cron.
3. Which Claude model to use for the forecast call (default suggestion:
   `claude-sonnet-4-6`).

Everything else in the docs/ folder is spec — implement it as written
unless it's ambiguous, in which case ask rather than guess.
