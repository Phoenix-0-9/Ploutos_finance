# Snapshot Schema

This is the contract between collectors → compiler → forecaster. Define
as a pydantic model in `src/compiler/build_snapshot.py` (or a
`schemas.py` if you prefer to separate it).

```json
{
  "date": "2026-06-20",
  "spot_rate": {
    "available": true,
    "spot": 109.42,
    "previous_close": 109.10,
    "change_pct": 0.29,
    "30d_high": 111.05,
    "30d_low": 107.88
  },
  "technicals": {
    "available": true,
    "rsi_14": 58.2,
    "sma_20": 108.9,
    "sma_50": 110.1,
    "macd": {"macd": 0.12, "signal": 0.08, "histogram": 0.04},
    "bollinger": {"upper": 111.0, "mid": 109.0, "lower": 107.0}
  },
  "uk_inflation": {
    "available": true,
    "cpi_yoy_pct": 2.3,
    "as_of": "2026-05-01",
    "source": "ONS"
  },
  "boe_policy": {
    "available": true,
    "bank_rate_pct": 4.25,
    "last_decision_date": "2026-06-18",
    "stance_summary": "...",
    "next_meeting_date": "2026-08-06"
  },
  "rbi_policy": {
    "available": true,
    "repo_rate_pct": 6.0,
    "last_decision_date": "2026-06-06",
    "stance_summary": "...",
    "next_meeting_date": "2026-08-05"
  },
  "news_headlines": {
    "available": true,
    "headlines": [
      {"title": "...", "source": "...", "published": "2026-06-19"}
    ]
  }
}
```

## Rules

- Every top-level section has an `"available"` boolean. If `false`, all
  other fields in that section may be absent — the forecaster prompt
  must handle this (state "data unavailable" rather than guessing).
- `date` is always the run date in `YYYY-MM-DD`, UTC.
- Never put secrets or raw API keys into the snapshot (it gets logged to
  `data/history.jsonl`, which may end up committed to git).
- Keep `news_headlines.headlines` capped at ~15 items to control prompt
  size/cost.
