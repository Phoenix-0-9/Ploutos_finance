"""Collector: technical indicators (RSI, SMA, MACD, Bollinger Bands).
Computed directly with pandas -- no pandas-ta/numba dependency needed.
Run standalone: python -m src.collectors.technicals
"""
import json


def _rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def collect() -> dict:
    try:
        from src.collectors._fx_history import get_history

        close = get_history()["Close"]

        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()

        return {
            "available": True,
            "rsi_14": round(float(_rsi(close).iloc[-1]), 4),
            "sma_20": round(float(sma20.iloc[-1]), 4),
            "sma_50": round(float(sma50.iloc[-1]), 4),
            "macd": {
                "macd": round(float(macd_line.iloc[-1]), 4),
                "signal": round(float(signal_line.iloc[-1]), 4),
                "histogram": round(float(histogram.iloc[-1]), 4),
            },
            "bollinger": {
                "upper": round(float((bb_mid + 2 * bb_std).iloc[-1]), 4),
                "mid": round(float(bb_mid.iloc[-1]), 4),
                "lower": round(float((bb_mid - 2 * bb_std).iloc[-1]), 4),
            },
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
