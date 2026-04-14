import feedparser


def fetch_feed_entries(rss_url: str) -> list[dict]:
    parsed = feedparser.parse(rss_url)
    if getattr(parsed, "bozo", False):
        raise parsed.bozo_exception
    return [dict(entry) for entry in parsed.entries]
