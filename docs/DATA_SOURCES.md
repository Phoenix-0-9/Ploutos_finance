# Data Sources

Each collector lives in `src/collectors/` and must expose a single
function `collect() -> dict`. Never raise — catch internally and return
an `"available": false` dict on failure.

## 1. Spot rate + history — `spot_rate.py`

- **Library**: `yfinance`
- **Ticker**: `GBPINR=X`
- Pull last ~90 days of daily OHLC for technicals (technicals.py will
  reuse this, consider a shared helper to avoid double-fetching).
- Return shape:
  ```python
  {
      "available": True,
      "date": "2026-06-20",
      "spot": 109.42,
      "previous_close": 109.10,
      "change_pct": 0.29,
      "30d_high": 111.05,
      "30d_low": 107.88
  }
  ```

## 2. Technical indicators — `technicals.py`

- **Library**: `pandas-ta` on top of the same `yfinance` history.
- Compute: RSI(14), SMA(20), SMA(50), MACD, Bollinger Bands (20, 2).
- Return shape:
  ```python
  {
      "available": True,
      "rsi_14": 58.2,
      "sma_20": 108.9,
      "sma_50": 110.1,
      "macd": {"macd": 0.12, "signal": 0.08, "histogram": 0.04},
      "bollinger": {"upper": 111.0, "mid": 109.0, "lower": 107.0}
  }
  ```

## 3. UK inflation — `uk_inflation.py`

- **Source**: ONS API (`https://api.ons.gov.uk/...`) — CPI annual rate
  series (series ID for CPIH or CPI YoY — confirm exact series id when
  implementing, ONS dataset browser: https://www.ons.gov.uk/economy/inflationandpriceindices).
- If the API is awkward, fallback: scrape the latest published figure
  from the ONS CPI release page, clearly marked with the release date.
- Return shape:
  ```python
  {
      "available": True,
      "cpi_yoy_pct": 2.3,
      "as_of": "2026-05-01",
      "source": "ONS"
  }
  ```

## 4. Bank of England policy — `boe_policy.py`

- **Source**: BoE website (`https://www.bankofengland.co.uk/monetary-policy/`)
  — no clean public "expectations" API exists. Two options:
  1. Fetch the latest MPC summary/minutes page and extract: current bank
     rate, vote split, and the policy statement's last paragraph (stance
     language).
  2. Simpler v1: hardcode the current bank rate (update manually after
     each MPC meeting, ~8x/year) plus pull recent news headlines
     mentioning "Bank of England" for stance signal (handled by news.py).
- Return shape:
  ```python
  {
      "available": True,
      "bank_rate_pct": 4.25,
      "last_decision_date": "2026-06-18",
      "stance_summary": "short text pulled from latest statement or news",
      "next_meeting_date": "2026-08-06"
  }
  ```

## 5. RBI policy — `rbi_policy.py`

- **Source**: RBI press releases (`https://www.rbi.org.in/`) — same
  situation as BoE, no clean expectations API.
- v1 approach: hardcode current repo rate (update after each MPC
  meeting, ~6x/year), pull RBI-related headlines via news.py for stance.
- Return shape: mirror `boe_policy.py`'s shape with `repo_rate_pct`
  instead of `bank_rate_pct`.

## 6. News headlines — `news.py`

- **Primary**: Google News RSS — no API key needed.
  Example feed URL pattern:
  `https://news.google.com/rss/search?q=GBP+INR+OR+%22Bank+of+England%22+OR+RBI&hl=en-GB`
- **Optional upgrade**: NewsAPI.org (free tier, key required, rate
  limited to 100 req/day) if RSS isn't rich enough.
- Pull top 10-15 headlines from the last 24-48 hours, dedupe, keep
  title + source + published date only (no full article scraping needed
  — Claude can reason from headlines).
- Return shape:
  ```python
  {
      "available": True,
      "headlines": [
          {"title": "...", "source": "...", "published": "2026-06-19"},
          ...
      ]
  }
  ```

## Rate limits / keys needed

| Source | Key required? | Free tier limit |
|---|---|---|
| yfinance | No | Unofficial, generous |
| ONS API | No | Generous |
| BoE / RBI pages | No | Be polite, cache daily |
| Google News RSS | No | Generous |
| NewsAPI.org (optional) | Yes | 100 req/day |
| Anthropic API | Yes | Pay-per-use |

Put any required keys in `.env` — see `.env.example`.
