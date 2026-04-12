from dataclasses import replace

from bs4 import BeautifulSoup

from nofomo.models import NormalizedItem
from nofomo.summarizer import build_summaries


def strip_html(value: str) -> str:
    if not value:
        return ""
    return " ".join(BeautifulSoup(value, "html.parser").get_text(" ").split())


def normalize_entry(source_id: str, platform: str, source_name: str, item_id: str, entry: dict) -> NormalizedItem:
    raw_summary = entry.get("summary") or entry.get("description") or ""
    normalized_text = strip_html(raw_summary or entry.get("title") or "")
    return NormalizedItem(
        item_id=item_id,
        source_id=source_id,
        platform=platform,
        source_name=source_name,
        title=(entry.get("title") or "(untitled)").strip(),
        url=(entry.get("link") or "").strip(),
        published_at=(entry.get("published") or entry.get("updated") or "").strip(),
        guid=(entry.get("id") or "").strip(),
        raw_summary=raw_summary,
        normalized_text=normalized_text,
        summary_short="",
        summary_long="",
    )


def attach_summaries(item: NormalizedItem) -> NormalizedItem:
    summary_short, summary_long = build_summaries(item.raw_summary, item.normalized_text)
    return replace(item, summary_short=summary_short, summary_long=summary_long)
