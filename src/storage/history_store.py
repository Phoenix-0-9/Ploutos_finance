"""Appends {date, snapshot, forecast} to data/history.jsonl (append-only),
writes output/latest_forecast.json and output/latest_forecast.md.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
HISTORY_FILE = DATA_DIR / "history.jsonl"
LATEST_JSON = OUTPUT_DIR / "latest_forecast.json"
LATEST_MD = OUTPUT_DIR / "latest_forecast.md"


def _endpoint(path: list, day: int) -> str:
    if not path or day < 1:
        return "N/A"
    closest = min(path, key=lambda p: abs(p["day"] - day))
    return f"{closest['rate']:.4f}"


def _render_markdown(snapshot: dict, forecast: dict) -> str:
    date = forecast.get("as_of_date", snapshot.get("date", "unknown"))
    spot = forecast.get("current_spot", 0.0)
    summary = forecast.get("summary", "")
    sc = forecast.get("scenarios", {})
    base = sc.get("base", {})
    bull = sc.get("bullish_gbp", {})
    bear = sc.get("bearish_gbp", {})
    drivers = forecast.get("key_drivers", [])
    gaps = forecast.get("data_gaps", [])
    disclaimer = forecast.get("disclaimer", "")
    appendix = forecast.get("appendix") or {}

    bp = base.get("path", [])
    bullp = bull.get("path", [])
    bearp = bear.get("path", [])

    drivers_md = "\n".join(f"- {d}" for d in drivers) or "- None"
    gaps_md = "\n".join(f"- {g}" for g in gaps) if gaps else "- None"

    sources = appendix.get("sources", [])
    sources_md = "\n".join(f"- {s}" for s in sources) if sources else "- None"

    abbrevs = appendix.get("abbreviations", [])
    abbrevs_md = (
        "\n".join(f"**{a['term']}** — {a['definition']}" for a in abbrevs)
        if abbrevs else "- None"
    )

    return f"""# GBP/INR Forecast — {date}

**Current spot:** {spot:.4f} INR per GBP
**Generated:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

---

## Overview

{summary}

## 30-Day Scenarios

| Scenario | Probability | Week 2 Rate | Week 4 Rate |
|----------|-------------|-------------|-------------|
| **Base** | {base.get("probability_pct", "?")}% | {_endpoint(bp, 14)} | {_endpoint(bp, 30)} |
| **Bullish GBP** | {bull.get("probability_pct", "?")}% | {_endpoint(bullp, 14)} | {_endpoint(bullp, 30)} |
| **Bearish GBP** | {bear.get("probability_pct", "?")}% | {_endpoint(bearp, 14)} | {_endpoint(bearp, 30)} |

### Base Case ({base.get("probability_pct", "?")}%)
{base.get("rationale", "")}

### Bullish GBP ({bull.get("probability_pct", "?")}%)
{bull.get("rationale", "")}

### Bearish GBP ({bear.get("probability_pct", "?")}%)
{bear.get("rationale", "")}

## Key Drivers

{drivers_md}

## Data Gaps

{gaps_md}

---

## Appendix

### Sources

{sources_md}

### Abbreviations & Key Terms

{abbrevs_md}

---
*{disclaimer}*
"""


def store(snapshot: dict, forecast: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    record = {"date": snapshot.get("date"), "snapshot": snapshot, "forecast": forecast}
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("Appended to %s", HISTORY_FILE)

    LATEST_JSON.write_text(json.dumps(forecast, indent=2), encoding="utf-8")
    logger.info("Wrote %s", LATEST_JSON)

    LATEST_MD.write_text(_render_markdown(snapshot, forecast), encoding="utf-8")
    logger.info("Wrote %s", LATEST_MD)
