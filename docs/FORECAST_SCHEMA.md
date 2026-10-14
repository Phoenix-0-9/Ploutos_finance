# Forecast Output Schema

This is what we ask Claude to return, and what `run_forecast.py` must
validate (pydantic) before storing.

```json
{
  "as_of_date": "2026-06-20",
  "current_spot": 109.42,
  "horizon_days": 30,
  "summary": "2-3 sentence plain-English summary of the overall outlook and key drivers.",
  "scenarios": {
    "base": {
      "probability_pct": 55,
      "rationale": "1-2 sentences on why this is the base case.",
      "path": [
        {"day": 1, "date": "2026-06-21", "rate": 109.5},
        {"day": 2, "date": "2026-06-22", "rate": 109.6}
      ]
    },
    "bullish_gbp": {
      "probability_pct": 25,
      "rationale": "1-2 sentences — what would need to happen for GBP to strengthen vs INR.",
      "path": [
        {"day": 1, "date": "2026-06-21", "rate": 110.0}
      ]
    },
    "bearish_gbp": {
      "probability_pct": 20,
      "rationale": "1-2 sentences — what would need to happen for GBP to weaken vs INR.",
      "path": [
        {"day": 1, "date": "2026-06-21", "rate": 108.8}
      ]
    }
  },
  "key_drivers": [
    "Short bullet on driver 1 (e.g. BoE rate stance)",
    "Short bullet on driver 2 (e.g. RBI policy)",
    "Short bullet on driver 3 (e.g. risk sentiment / news)"
  ],
  "data_gaps": [
    "Any snapshot sections marked unavailable, so the user knows what was missing."
  ],
  "disclaimer": "Short-horizon FX forecasts are not reliable trading signals. This is for personal budgeting awareness only, not financial advice."
}
```

## Validation rules

- `scenarios.*.probability_pct` across the three scenarios should sum to
  ~100 (allow 95-105 tolerance, don't reject for minor rounding).
- `path` arrays should have exactly `horizon_days` entries — if Claude
  returns fewer (e.g. weekly points instead of daily), that's acceptable
  IF it's deliberate; instruct in the prompt that daily granularity is
  preferred but weekly is acceptable as a fallback. Validate length is
  one of {30 (daily), ~4-5 (weekly)} and tag which granularity it used.
- If JSON parsing or schema validation fails twice, log raw text to
  `data/errors/<date>.txt` and exit non-zero — do not store partial/
  malformed forecasts in `history.jsonl`.
