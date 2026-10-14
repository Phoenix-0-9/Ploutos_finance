"""Collector: Bank of England policy rate + stance.
v1: bank rate is hardcoded — update manually after each MPC meeting (~8x/year).
See https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate
Run standalone: python -m src.collectors.boe_policy
"""
import json

# Update after each MPC decision. Last updated: 2026-06-18.
_BANK_RATE_PCT = 3.75
_LAST_DECISION_DATE = "2026-06-18"
_NEXT_MEETING_DATE = "2026-08-06"


def _stance_from_news() -> str:
    try:
        import feedparser
        url = (
            "https://news.google.com/rss/search"
            "?q=%22Bank+of+England%22+rate+decision&hl=en-GB&gl=GB&ceid=GB:en"
        )
        feed = feedparser.parse(url)
        titles = [e.title for e in feed.entries[:3] if hasattr(e, "title")]
        if titles:
            return "Recent headlines: " + "; ".join(titles)[:300]
    except Exception:
        pass
    return "Stance language unavailable."


def collect() -> dict:
    try:
        return {
            "available": True,
            "bank_rate_pct": _BANK_RATE_PCT,
            "last_decision_date": _LAST_DECISION_DATE,
            "stance_summary": _stance_from_news(),
            "next_meeting_date": _NEXT_MEETING_DATE,
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
