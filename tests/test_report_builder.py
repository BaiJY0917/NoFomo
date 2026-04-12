from nofomo.models import NormalizedItem
from nofomo.report_builder import build_daily_report


def make_item(item_id: str, is_highlight: bool) -> NormalizedItem:
    return NormalizedItem(
        item_id=item_id,
        source_id="source-a",
        platform="x",
        source_name="X User",
        title=f"Title {item_id}",
        url=f"https://example.com/{item_id}",
        published_at="2026-04-11T08:00:00Z",
        guid=item_id,
        raw_summary="",
        normalized_text="AI agent launch",
        summary_short="AI agent launch",
        summary_long="AI agent launch",
        matched_keywords=["agent"] if is_highlight else [],
        is_highlight=is_highlight,
    )


def test_build_daily_report_splits_highlights_and_normal_items():
    report = build_daily_report(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        items=[make_item("one", True), make_item("two", False)],
        total_sources=1,
        failed_sources=["broken-feed"],
    )

    assert report.total_new_items == 2
    assert report.total_highlights == 1
    assert [item.item_id for item in report.highlights] == ["one"]
    assert [item.item_id for item in report.normal_items] == ["two"]
