from dataclasses import replace

from nofomo.models import NormalizedItem


def apply_keywords(item: NormalizedItem, keywords: list[str]) -> NormalizedItem:
    haystack = " ".join([item.title, item.summary_short, item.summary_long, item.normalized_text]).lower()
    matched_keywords = [keyword for keyword in keywords if keyword in haystack]
    return replace(item, matched_keywords=matched_keywords, is_highlight=bool(matched_keywords))
