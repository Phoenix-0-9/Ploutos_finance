"""Merges all collector outputs into the snapshot shape from SNAPSHOT_SCHEMA.md.
Degrades gracefully if any collector fails — marks section available=false,
never crashes the whole pipeline.
Run standalone: python -m src.compiler.build_snapshot
"""
import importlib
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schema (validates the merged snapshot before passing to forecaster)
# ---------------------------------------------------------------------------

class MacdData(BaseModel):
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None


class BollingerData(BaseModel):
    upper: Optional[float] = None
    mid: Optional[float] = None
    lower: Optional[float] = None


class SpotRateSection(BaseModel):
    available: bool
    date: Optional[str] = None
    spot: Optional[float] = None
    previous_close: Optional[float] = None
    change_pct: Optional[float] = None
    high_30d: Optional[float] = Field(None, alias="30d_high")
    low_30d: Optional[float] = Field(None, alias="30d_low")
    reason: Optional[str] = None
    model_config = {"populate_by_name": True}


class TechnicalsSection(BaseModel):
    available: bool
    rsi_14: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    macd: Optional[MacdData] = None
    bollinger: Optional[BollingerData] = None
    reason: Optional[str] = None


class UkInflationSection(BaseModel):
    available: bool
    cpi_yoy_pct: Optional[float] = None
    as_of: Optional[str] = None
    source: Optional[str] = None
    reason: Optional[str] = None


class BoePolicySection(BaseModel):
    available: bool
    bank_rate_pct: Optional[float] = None
    last_decision_date: Optional[str] = None
    stance_summary: Optional[str] = None
    next_meeting_date: Optional[str] = None
    reason: Optional[str] = None


class RbiPolicySection(BaseModel):
    available: bool
    repo_rate_pct: Optional[float] = None
    last_decision_date: Optional[str] = None
    stance_summary: Optional[str] = None
    next_meeting_date: Optional[str] = None
    reason: Optional[str] = None


class Headline(BaseModel):
    title: str
    source: str
    published: str


class NewsSection(BaseModel):
    available: bool
    headlines: Optional[List[Headline]] = None
    reason: Optional[str] = None


class Snapshot(BaseModel):
    date: str
    spot_rate: SpotRateSection
    technicals: TechnicalsSection
    uk_inflation: UkInflationSection
    boe_policy: BoePolicySection
    rbi_policy: RbiPolicySection
    news_headlines: NewsSection


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _safe_collect(module_path: str) -> dict:
    try:
        mod = importlib.import_module(module_path)
        result = mod.collect()
        if not isinstance(result, dict):
            return {"available": False, "reason": f"{module_path} returned non-dict"}
        return result
    except Exception as e:
        logger.warning("Collector %s failed: %s", module_path, e)
        return {"available": False, "reason": str(e)}


def build_snapshot() -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    raw = {
        "date": today,
        "spot_rate": _safe_collect("src.collectors.spot_rate"),
        "technicals": _safe_collect("src.collectors.technicals"),
        "uk_inflation": _safe_collect("src.collectors.uk_inflation"),
        "boe_policy": _safe_collect("src.collectors.boe_policy"),
        "rbi_policy": _safe_collect("src.collectors.rbi_policy"),
        "news_headlines": _safe_collect("src.collectors.news"),
    }

    try:
        Snapshot.model_validate(raw)
    except Exception as e:
        logger.warning("Snapshot schema warning: %s", e)

    return raw


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(build_snapshot(), indent=2))
