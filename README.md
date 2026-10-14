# GBP/INR Forecaster Agent

A personal daily agent that estimates GBP/INR exchange rates for the
next 30 days, to help plan transfers for UK tuition fees and living
expenses from India.

It pulls:
- GBP/INR spot rate + price history (for technical indicators)
- UK CPI inflation data
- Bank of England policy statements
- RBI policy statements
- Recent GBP/INR-relevant news headlines
- Technical indicators (RSI, moving averages, MACD)

...compiles all of it into one snapshot, sends it to Claude with a
structured forecasting prompt, and stores/delivers a base / bullish /
bearish 30-day scenario forecast with probabilities.

**This is not financial advice and not a trading tool.** It's a
decision-support aid for timing personal remittances.

## Quick start

```bash
git clone <this-repo>
cd gbpinr-forecaster
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your ANTHROPIC_API_KEY etc.
python -m src.main
```

Output appears in `output/latest_forecast.md` and `output/latest_forecast.json`.
Historical runs accumulate in `data/history.jsonl`.

## Project structure

```
gbpinr-forecaster/
├── CLAUDE.md                  # build instructions for Claude Code
├── README.md                  # this file
├── requirements.txt
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md        # system design
│   ├── DATA_SOURCES.md        # exact APIs/libraries per data source
│   ├── SNAPSHOT_SCHEMA.md     # shape of the daily data snapshot
│   ├── FORECAST_SCHEMA.md     # shape of the model's forecast output
│   ├── CLAUDE_API_NOTES.md    # how to call the Claude API correctly
│   └── DELIVERY_OPTIONS.md    # email / Telegram / Sheets options
├── prompts/
│   └── forecast_prompt.md     # the prompt template sent to Claude
├── src/
│   ├── config.py              # env var loading
│   ├── main.py                # orchestrator entry point
│   ├── collectors/            # one file per data source
│   │   ├── spot_rate.py
│   │   ├── technicals.py
│   │   ├── uk_inflation.py
│   │   ├── boe_policy.py
│   │   ├── rbi_policy.py
│   │   └── news.py
│   ├── compiler/
│   │   └── build_snapshot.py
│   ├── forecaster/
│   │   └── run_forecast.py
│   └── storage/
│       ├── history_store.py
│       └── notify.py
├── data/
│   └── history.jsonl          # append-only log of past snapshots+forecasts
├── output/
│   ├── latest_forecast.json
│   └── latest_forecast.md
├── tests/
└── .github/workflows/
    └── daily_forecast.yml     # daily cron via GitHub Actions
```

## Running on a schedule

See `docs/DELIVERY_OPTIONS.md` and `.github/workflows/daily_forecast.yml`.
Default plan: GitHub Actions cron, free tier, runs once a day, commits
results back to the repo and (optionally) sends a Telegram/email push.

## Disclaimer

FX forecasting over a 30-day horizon is inherently unreliable — no
model, AI or otherwise, reliably predicts currency moves at this
horizon. Treat output as situational awareness for budgeting decisions,
not a trading signal.
