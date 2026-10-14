"""Collector: recent GBP/INR-relevant news headlines via Google News RSS.
Run standalone: python -m src.collectors.news
"""
import json
from datetime import datetime, timezone

import feedparser

_RSS_FEEDS = [
    "https://news.google.com/rss/search?q=GBP+INR+OR+%22Bank+of+England%22+OR+RBI+exchange+rate&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=pound+rupee+OR+sterling+rupee&hl=en-IN&gl=IN&ceid=IN:en",
]


def _parse_date(entry) -> str:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def collect() -> dict:
    try:
        seen: set = set()
        headlines = []
        for url in _RSS_FEEDS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                source = ""
                if hasattr(entry, "source") and entry.source:
                    source = getattr(entry.source, "title", "")
                headlines.append({
                    "title": title,
                    "source": source,
                    "published": _parse_date(entry),
                })
                if len(headlines) >= 15:
                    break
            if len(headlines) >= 15:
                break
        return {"available": True, "headlines": headlines}
    except Exception as e:
        return {"available": False, "reason": str(e)}


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
