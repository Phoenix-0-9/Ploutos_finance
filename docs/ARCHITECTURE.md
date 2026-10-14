# Architecture

## Pipeline

```
main.py (orchestrator)
   │
   ├─ 1. collectors/*.py  ──► each returns a dict, never raises uncaught
   │                          (catches its own errors, returns {"error": "..."} )
   │
   ├─ 2. compiler/build_snapshot.py
   │       merges collector outputs → snapshot.json (see SNAPSHOT_SCHEMA.md)
   │       writes data/snapshots/<date>.json (optional, for debugging)
   │
   ├─ 3. forecaster/run_forecast.py
   │       loads prompts/forecast_prompt.md
   │       fills template with snapshot fields
   │       calls Claude API → expects strict JSON back
   │       validates against FORECAST_SCHEMA.md (pydantic)
   │       retries once if invalid
   │
   ├─ 4. storage/history_store.py
   │       appends {date, snapshot, forecast} to data/history.jsonl
   │       writes output/latest_forecast.json
   │       renders output/latest_forecast.md (human-readable)
   │
   └─ 5. storage/notify.py (optional)
           sends output/latest_forecast.md via email/Telegram
```

## Design principles

1. **Each collector is independent and fault-tolerant.** If RBI's site is
   down or NewsAPI rate-limits you, the pipeline still runs — that
   collector's section is marked null in the snapshot, and the prompt
   tells the model "data unavailable for X" rather than crashing.

2. **The snapshot is the contract.** Collectors → snapshot → forecaster
   are decoupled by the schema in `SNAPSHOT_SCHEMA.md`. You can swap a
   data source's implementation without touching the forecaster, as
   long as the output dict shape doesn't change.

3. **Forecast output is structured, not prose.** Asking Claude for JSON
   (base/bull/bear scenarios with probabilities + reasoning) makes the
   output: (a) easy to chart over time, (b) easy to compare predicted vs
   actual after the fact, (c) easy to render into the markdown summary.

4. **History is append-only.** `data/history.jsonl` never gets rewritten,
   only appended to. This lets you eventually backtest: "what did the
   model predict 20 days ago for today, and how far off was it?"

5. **No execution, no trading.** This system only informs a human
   decision (when to convert INR→GBP). It never places orders or talks
   to a brokerage/bank API.

## Data flow example (single day)

1. Collectors run in parallel (or sequence — doesn't matter, it's fast):
   spot rate, technicals, UK CPI, BoE statement, RBI statement, news
   headlines.
2. Compiler merges them into one JSON object, e.g.:
   ```json
   {
     "date": "2026-06-20",
     "spot_rate": {...},
     "technicals": {...},
     "uk_inflation": {...},
     "boe_policy": {...},
     "rbi_policy": {...},
     "news_headlines": [...]
   }
   ```
3. This snapshot is interpolated into `prompts/forecast_prompt.md` and
   sent to Claude.
4. Claude returns JSON matching `FORECAST_SCHEMA.md`: 30 daily points
   under base/bull/bear, each with a rate + probability + one-line
   rationale, plus an overall summary.
5. Stored + rendered + (optionally) pushed to the user.

## Failure modes to handle explicitly

- A collector times out or 4xx/5xxs → return `{"available": false,
  "reason": "..."}` for that section, don't crash main.py.
- Claude returns malformed JSON → retry once with a stricter
  "return ONLY valid JSON" reminder appended; if it fails again, log raw
  output to `data/errors/<date>.txt` and exit 1 (this *should* fail the
  pipeline, since the core output is broken).
- GitHub Actions secret missing → fail fast and clearly in `config.py`
  with a readable error message, not a stack trace.
