from nofomo.keyword_matcher import apply_keywords
from nofomo.models import NormalizedItem


def make_item() -> NormalizedItem:
    return NormalizedItem(
        item_id="abc123def456",
        source_id="source-a",
        platform="x",
        source_name="X User",
        title="AI agent launch",
        url="https://example.com/post-1",
        published_at="2026-04-11T08:00:00Z",
        guid="guid-1",
        raw_summary="",
        normalized_text="AI agent launch with automation workflow",
        summary_short="AI agent launch with automation workflow",
        summary_long="AI agent launch with automation workflow",
    )


def test_apply_keywords_marks_highlight_when_keyword_matches():
    item = apply_keywords(make_item(), ["agent", "growth"])

    assert item.is_highlight is True
    assert item.matched_keywords == ["agent"]
