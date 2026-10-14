"""Mocked tests for the forecaster — no real API calls."""
import json
import pytest
from unittest.mock import patch

from src.forecaster.run_forecast import Forecast, _strip_fences

_PATH_30 = [{"day": i, "date": f"2026-07-{i:02d}", "rate": 109.0 + i * 0.01} for i in range(1, 31)]

VALID_FORECAST = {
    "as_of_date": "2026-06-22",
    "current_spot": 109.42,
    "horizon_days": 30,
    "summary": "GBP/INR expected to remain stable over the next 30 days.",
    "scenarios": {
        "base": {"probability_pct": 55, "rationale": "Stable macro.", "path": _PATH_30},
        "bullish_gbp": {"probability_pct": 25, "rationale": "BoE hawkish.", "path": _PATH_30},
        "bearish_gbp": {"probability_pct": 20, "rationale": "Risk-off.", "path": _PATH_30},
    },
    "key_drivers": ["BoE rate hold", "RBI policy", "Risk sentiment"],
    "data_gaps": [],
    "disclaimer": "Short-horizon FX forecasts are not reliable trading signals. This is for personal budgeting awareness only, not financial advice.",
}

MOCK_SNAPSHOT = {
    "date": "2026-06-22",
    "spot_rate": {"available": True, "spot": 109.42, "previous_close": 109.1,
                  "change_pct": 0.29, "30d_high": 111.0, "30d_low": 107.0},
    "technicals": {"available": False, "reason": "test"},
    "uk_inflation": {"available": False, "reason": "test"},
    "boe_policy": {"available": False, "reason": "test"},
    "rbi_policy": {"available": False, "reason": "test"},
    "news_headlines": {"available": False, "reason": "test"},
}


def test_forecast_schema_validates_valid():
    f = Forecast.model_validate(VALID_FORECAST)
    assert f.scenarios.base.probability_pct == 55


def test_forecast_schema_rejects_bad_probabilities():
    bad = json.loads(json.dumps(VALID_FORECAST))
    bad["scenarios"]["base"]["probability_pct"] = 80  # sum = 125
    with pytest.raises(Exception):
        Forecast.model_validate(bad)


def test_strip_fences_removes_markdown():
    raw = "```json\n{\"key\": 1}\n```"
    assert _strip_fences(raw) == '{"key": 1}'


def test_strip_fences_passthrough():
    raw = '{"key": 1}'
    assert _strip_fences(raw) == raw


@patch("src.forecaster.run_forecast._call_claude")
def test_run_forecast_success(mock_claude):
    from src.forecaster.run_forecast import run_forecast
    mock_claude.return_value = json.dumps(VALID_FORECAST)
    result = run_forecast(MOCK_SNAPSHOT)
    assert result["as_of_date"] == "2026-06-22"
    assert result["scenarios"]["base"]["probability_pct"] == 55
    mock_claude.assert_called_once()


@patch("src.forecaster.run_forecast._save_error")
@patch("src.forecaster.run_forecast._call_claude")
def test_run_forecast_retries_and_exits_on_bad_json(mock_claude, mock_save_error):
    from src.forecaster.run_forecast import run_forecast
    mock_claude.return_value = "this is not json at all"
    with pytest.raises(SystemExit):
        run_forecast(MOCK_SNAPSHOT)
    assert mock_claude.call_count == 2
    mock_save_error.assert_called_once()
