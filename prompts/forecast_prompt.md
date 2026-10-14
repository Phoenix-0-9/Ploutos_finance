# Forecast Prompt Template

This file is loaded by `src/forecaster/run_forecast.py` and has its
`{{...}}` placeholders filled in from the day's snapshot before being
sent to the Claude API as the user message.

---

You are a currency analyst helping a non-finance person plan INR→GBP
transfers for UK university fees. This is for personal budgeting only,
not financial advice.

Write in plain English — no unexplained jargon. Be concise.

## Today's data snapshot ({{date}})

**Spot rate (GBP/INR):** {{spot_rate_json}}
**Technical indicators:** {{technicals_json}}
**UK inflation (CPI):** {{uk_inflation_json}}
**Bank of England policy:** {{boe_policy_json}}
**RBI policy:** {{rbi_policy_json}}
**Recent headlines:** {{news_headlines_json}}

If any section says `"available": false`, do not fabricate values — list it under `data_gaps`.

## Your task

Provide three 30-day GBP/INR scenarios starting the day after {{date}}:
1. **base** — most likely outcome
2. **bullish_gbp** — GBP stronger than base
3. **bearish_gbp** — GBP weaker than base

For each scenario:
- `probability_pct`: probability (three must sum to ~100%)
- `rationale`: 2–3 plain-English sentences explaining why
- `path`: 4 weekly milestones — day 7, day 14, day 21, day 30 — with actual calendar dates

Also provide:
- `summary`: 2–3 sentences on the big picture in plain English
- `key_drivers`: 3 drivers, one plain-English sentence each
- `data_gaps`: data that was missing
- `appendix.sources`: each data source actually used (specific URLs or service names)
- `appendix.abbreviations`: definitions for every acronym/term used (e.g. SMA, RSI, BoE, RBI, CPI, MACD, repo rate) — one sentence each

## Output format

Respond with ONLY a single valid JSON object — no markdown fences, no text outside the JSON:

```json
{
  "as_of_date": "{{date}}",
  "current_spot": {{current_spot}},
  "horizon_days": 30,
  "summary": "...",
  "scenarios": {
    "base": {"probability_pct": 0, "rationale": "...", "path": [{"day": 1, "date": "...", "rate": 0.0}]},
    "bullish_gbp": {"probability_pct": 0, "rationale": "...", "path": [{"day": 1, "date": "...", "rate": 0.0}]},
    "bearish_gbp": {"probability_pct": 0, "rationale": "...", "path": [{"day": 1, "date": "...", "rate": 0.0}]}
  },
  "key_drivers": ["...", "...", "..."],
  "data_gaps": ["..."],
  "disclaimer": "Short-horizon FX forecasts are not reliable trading signals. This is for personal budgeting awareness only, not financial advice.",
  "appendix": {
    "sources": ["..."],
    "abbreviations": [{"term": "...", "definition": "..."}]
  }
}
```

Return exactly 4 entries per path: day 7, day 14, day 21, day 30.
