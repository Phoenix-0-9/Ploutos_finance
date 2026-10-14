"""Shared yfinance downloader — cached per-process so spot_rate and
technicals collectors don't double-fetch.
"""
from functools import lru_cache

import pandas as pd
import yfinance as yf


@lru_cache(maxsize=1)
def get_history(period: str = "90d") -> pd.DataFrame:
    df = yf.Ticker("GBPINR=X").history(period=period)
    if df.empty:
        raise ValueError("yfinance returned an empty dataframe for GBPINR=X")
    return df
