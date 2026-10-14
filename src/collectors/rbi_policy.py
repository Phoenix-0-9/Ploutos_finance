"""Collector: RBI policy rate + stance.
v1: repo rate is hardcoded — update manually after each MPC meeting (~6x/year).
See https://www.rbi.org.in/
Run standalone: python -m src.collectors.rbi_policy
"""
import json

# Update after each RBI MPC decision.
_REPO_RATE_PCT = 6.0
_LAST_DECISION_DATE = "2026-06-06"
_NEXT_MEETING_DATE = "2026-08-05"


def _stance_from_news() -> str:
    try:
        import feedparser
        url = (
            "https://news.google.com/rss/search"
            "?q=RBI+%22repo+rate%22+OR+%22monetary+policy%22&hl=en-IN&gl=IN&ceid=IN:en"
        )
        feed = feedparser.parse(url)
        titles = [e.title for e in feed.entries[:3] if hasattr(e, "title")]
        if titles:
            return "Recent headlines: " + "; ".join(titles)[:300]
    except Exception:
        pass
    return "RBI stance language unavailable."


def collect() -> dict:
    try:
        return {
            "available": True,
            "repo_rate_pct": _REPO_RATE_PCT,
            "last_decision_date": _LAST_DECISION_DATE,
            "stance_summary": _stance_from_news(),
            "next_meeting_date": _NEXT_MEETING_DATE,
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
