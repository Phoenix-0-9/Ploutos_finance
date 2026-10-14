"""Collector: UK CPI inflation rate from the ONS API.
Run standalone: python -m src.collectors.uk_inflation
"""
import json
from datetime import datetime

import httpx

_ONS_ENDPOINTS = [
    "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l55o/data",
    "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/data",
]


def collect() -> dict:
    try:
        data = None
        for url in _ONS_ENDPOINTS:
            try:
                r = httpx.get(url, timeout=15, follow_redirects=True)
                r.raise_for_status()
                data = r.json()
                break
            except Exception:
                continue

        if data is None:
            return {"available": False, "reason": "All ONS API endpoints failed"}

        months = data.get("months") or []
        if not months:
            return {"available": False, "reason": "No monthly data in ONS response"}

        latest = months[-1]
        raw_date = latest.get("date", "")
        val = float(latest.get("value", "0"))

        try:
            parsed = datetime.strptime(raw_date.strip(), "%Y %b")
            as_of = parsed.strftime("%Y-%m-01")
        except ValueError:
            as_of = raw_date

        return {
            "available": True,
            "cpi_yoy_pct": round(val, 4),
            "as_of": as_of,
            "source": "ONS",
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
