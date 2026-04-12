import json
from pathlib import Path

from nofomo.models import DailyReport, FeedbackRecord, NormalizedItem
from nofomo.report_builder import build_daily_report
from nofomo.report_store import append_feedback_record, load_report_by_item_id, save_daily_report


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


def test_save_daily_report_writes_json(tmp_path: Path):
    report = DailyReport(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        total_new_items=1,
        total_sources=1,
        total_highlights=0,
        failed_sources=[],
        highlights=[],
        normal_items=[make_item("item-1", False)],
    )

    save_daily_report(tmp_path / "reports", report)

    payload = json.loads((tmp_path / "reports" / "2026-04-11.json").read_text(encoding="utf-8"))
    assert payload["report_date"] == "2026-04-11"
    assert payload["normal_items"][0]["item_id"] == "item-1"


def test_load_report_by_item_id_finds_item_in_saved_archive(tmp_path: Path):
    report = DailyReport(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        total_new_items=1,
        total_sources=1,
        total_highlights=0,
        failed_sources=[],
        highlights=[],
        normal_items=[make_item("item-1", False)],
    )
    save_daily_report(tmp_path / "reports", report)

    found = load_report_by_item_id(tmp_path / "reports", "item-1")

    assert found is not None
    assert found["report_date"] == "2026-04-11"
    assert found["item"]["item_id"] == "item-1"
