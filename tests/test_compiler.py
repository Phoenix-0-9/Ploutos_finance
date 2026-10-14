"""Unit tests for the snapshot compiler."""
from unittest.mock import patch

from src.compiler.build_snapshot import Snapshot, build_snapshot


def _spot():
    return {
        "available": True,
        "date": "2026-06-22",
        "spot": 109.42,
        "previous_close": 109.10,
        "change_pct": 0.29,
        "30d_high": 111.05,
        "30d_low": 107.88,
    }

def _technicals():
    return {
        "available": True,
        "rsi_14": 58.2,
        "sma_20": 108.9,
        "sma_50": 110.1,
        "macd": {"macd": 0.12, "signal": 0.08, "histogram": 0.04},
        "bollinger": {"upper": 111.0, "mid": 109.0, "lower": 107.0},
    }

def _uk_inflation():
    return {"available": True, "cpi_yoy_pct": 2.3, "as_of": "2026-05-01", "source": "ONS"}

def _boe():
    return {
        "available": True,
        "bank_rate_pct": 4.25,
        "last_decision_date": "2026-06-18",
        "stance_summary": "Holding",
        "next_meeting_date": "2026-08-06",
    }

def _rbi():
    return {
        "available": True,
        "repo_rate_pct": 6.0,
        "last_decision_date": "2026-06-06",
        "stance_summary": "Accommodative",
        "next_meeting_date": "2026-08-05",
    }

def _news():
    return {
        "available": True,
        "headlines": [{"title": "GBP rises", "source": "BBC", "published": "2026-06-22"}],
    }

def _unavailable(reason="test failure"):
    return {"available": False, "reason": reason}


@patch("src.compiler.build_snapshot._safe_collect")
def test_full_snapshot_validates(mock_collect):
    """All collectors succeed — snapshot validates against schema."""
    data = {
        "src.collectors.spot_rate": _spot(),
        "src.collectors.technicals": _technicals(),
        "src.collectors.uk_inflation": _uk_inflation(),
        "src.collectors.boe_policy": _boe(),
        "src.collectors.rbi_policy": _rbi(),
        "src.collectors.news": _news(),
    }
    mock_collect.side_effect = lambda path: data[path]
    snapshot = build_snapshot()
    assert snapshot["spot_rate"]["available"] is True
    Snapshot.model_validate(snapshot)


@patch("src.compiler.build_snapshot._safe_collect")
def test_partial_failure_does_not_crash(mock_collect):
    """Some collectors failing still produces a valid snapshot dict."""
    data = {
        "src.collectors.spot_rate": _spot(),
        "src.collectors.technicals": _unavailable("pandas-ta error"),
        "src.collectors.uk_inflation": _unavailable("ONS timeout"),
        "src.collectors.boe_policy": _boe(),
        "src.collectors.rbi_policy": _rbi(),
        "src.collectors.news": _unavailable("feedparser error"),
    }
    mock_collect.side_effect = lambda path: data[path]
    snapshot = build_snapshot()
    assert snapshot["technicals"]["available"] is False
    assert snapshot["news_headlines"]["available"] is False
    assert snapshot["spot_rate"]["available"] is True


@patch("src.compiler.build_snapshot._safe_collect")
def test_all_collectors_fail(mock_collect):
    """All collectors failing still returns a dict with a date field."""
    mock_collect.return_value = _unavailable()
    snapshot = build_snapshot()
    assert "date" in snapshot
    assert snapshot["spot_rate"]["available"] is False
