"""Fills prompts/forecast_prompt.md with the snapshot, calls Claude,
validates the JSON response. Retries once on parse/schema failure.
Exits non-zero if both attempts fail.
"""
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import anthropic
from pydantic import BaseModel, model_validator

from src import config

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "forecast_prompt.md"
ERRORS_DIR = Path(__file__).parent.parent.parent / "data" / "errors"


# ---------------------------------------------------------------------------
# Pydantic forecast schema
# ---------------------------------------------------------------------------

class DayPoint(BaseModel):
    day: int
    date: str
    rate: float


class Scenario(BaseModel):
    probability_pct: int
    rationale: str
    path: List[DayPoint]


class Scenarios(BaseModel):
    base: Scenario
    bullish_gbp: Scenario
    bearish_gbp: Scenario


class AbbreviationEntry(BaseModel):
    term: str
    definition: str


class Appendix(BaseModel):
    sources: List[str]
    abbreviations: List[AbbreviationEntry]


class Forecast(BaseModel):
    as_of_date: str
    current_spot: float
    horizon_days: int
    summary: str
    scenarios: Scenarios
    key_drivers: List[str]
    data_gaps: List[str]
    disclaimer: str
    appendix: Optional[Appendix] = None

    @model_validator(mode="after")
    def check_probabilities(self) -> "Forecast":
        total = (
            self.scenarios.base.probability_pct
            + self.scenarios.bullish_gbp.probability_pct
            + self.scenarios.bearish_gbp.probability_pct
        )
        if not (95 <= total <= 105):
            raise ValueError(
                f"Scenario probabilities sum to {total}, expected 95-105"
            )
        return self


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fill_prompt(snapshot: dict) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    spot_data = snapshot.get("spot_rate", {})
    current_spot = (
        spot_data.get("spot", 0.0) if spot_data.get("available") else 0.0
    )
    replacements = {
        "{{date}}": snapshot["date"],
        "{{current_spot}}": str(current_spot),
        "{{spot_rate_json}}": json.dumps(snapshot.get("spot_rate", {"available": False}), indent=2),
        "{{technicals_json}}": json.dumps(snapshot.get("technicals", {"available": False}), indent=2),
        "{{uk_inflation_json}}": json.dumps(snapshot.get("uk_inflation", {"available": False}), indent=2),
        "{{boe_policy_json}}": json.dumps(snapshot.get("boe_policy", {"available": False}), indent=2),
        "{{rbi_policy_json}}": json.dumps(snapshot.get("rbi_policy", {"available": False}), indent=2),
        "{{news_headlines_json}}": json.dumps(snapshot.get("news_headlines", {"available": False}), indent=2),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def _strip_fences(text: str) -> str:
    # Handle ```json ... ``` anywhere in the response (including with preamble text)
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        return fence_match.group(1).strip()
    # Fall back to extracting the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


def _call_claude(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _save_error(date: str, raw: str) -> None:
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    path = ERRORS_DIR / f"{date}.txt"
    path.write_text(raw, encoding="utf-8")
    logger.error("Raw Claude response saved to %s", path)


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def run_forecast(snapshot: dict) -> dict:
    prompt = _fill_prompt(snapshot)
    date = snapshot["date"]
    last_raw = ""

    for attempt in range(2):
        if attempt == 1:
            prompt += (
                "\n\nYour previous response was not valid JSON matching the required schema. "
                "Return ONLY the corrected JSON object -- no markdown fences, no explanation."
            )
        try:
            last_raw = _call_claude(prompt)
            parsed = json.loads(_strip_fences(last_raw))
            forecast = Forecast.model_validate(parsed)
            return forecast.model_dump()
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Attempt %d failed: %s", attempt + 1, e)

    _save_error(date, last_raw)
    logger.error("Forecast failed after 2 attempts — exiting non-zero.")
    sys.exit(1)
