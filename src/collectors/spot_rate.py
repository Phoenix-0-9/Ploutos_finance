"""Collector: GBP/INR spot rate + recent OHLC history.
Run standalone: python -m src.collectors.spot_rate
"""
import json


def collect() -> dict:
    try:
        from src.collectors._fx_history import get_history
        df = get_history()
        close = df["Close"]
        spot = round(float(close.iloc[-1]), 4)
        prev_close = round(float(close.iloc[-2]), 4)
        change_pct = round((spot - prev_close) / prev_close * 100, 4)
        last_30 = close.iloc[-30:]
        return {
            "available": True,
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "spot": spot,
            "previous_close": prev_close,
            "change_pct": change_pct,
            "30d_high": round(float(last_30.max()), 4),
            "30d_low": round(float(last_30.min()), 4),
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
