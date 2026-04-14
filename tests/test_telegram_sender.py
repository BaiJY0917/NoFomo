from nofomo.models import DailyReport, NormalizedItem, TelegramConfig
from nofomo.telegram_sender import build_digest_messages, send_messages


def make_item(item_id: str, highlight: bool) -> NormalizedItem:
    return NormalizedItem(
        item_id=item_id,
        source_id="source-a",
        platform="x",
        source_name="X User",
        title="AI agent launch",
        url="https://example.com/post-1",
        published_at="2026-04-11T08:00:00Z",
        guid=item_id,
        raw_summary="",
        normalized_text="AI agent launch",
        summary_short="Short summary",
        summary_long="Long summary",
        matched_keywords=["agent"] if highlight else [],
        is_highlight=highlight,
    )


def test_build_digest_messages_returns_overview_then_item_messages():
    report = DailyReport(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        total_new_items=2,
        total_sources=1,
        total_highlights=1,
        failed_sources=["broken-feed"],
        highlights=[make_item("item-1", True)],
        normal_items=[make_item("item-2", False)],
    )

    messages = build_digest_messages(report)

    assert len(messages) == 3
    assert "今日概览" in messages[0]
    assert "/like item-1" in messages[1]
    assert "/dislike item-2" in messages[2]


def test_send_messages_posts_each_message(mocker):
    post = mocker.patch("nofomo.telegram_sender.requests.post")
    post.return_value.raise_for_status.return_value = None
    config = TelegramConfig(bot_token="token123", chat_id="chat456")

    send_messages(config, ["message one", "message two"])

    assert post.call_count == 2
