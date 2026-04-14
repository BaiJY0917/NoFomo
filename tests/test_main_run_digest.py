import json
from datetime import UTC, datetime
from pathlib import Path

from nofomo.main import main, run_digest


def test_run_digest_saves_report_sends_messages_and_updates_seen(mocker, tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "data").mkdir()
    (root / "config" / "sources.yaml").write_text(
        "sources:\n  - id: source-a\n    platform: x\n    name: X User\n    rss_url: https://example.com/feed.xml\n",
        encoding="utf-8",
    )
    (root / "config" / "keywords.yaml").write_text("keywords:\n  - agent\n", encoding="utf-8")
    (root / "config" / "telegram.yaml").write_text("bot_token: token123\nchat_id: chat456\n", encoding="utf-8")

    mocker.patch("nofomo.main.datetime").now.return_value = datetime(2026, 4, 11, 9, 0, tzinfo=UTC)
    mocker.patch("nofomo.main.fetch_feed_entries", return_value=[{
        "title": "AI agent launch",
        "link": "https://example.com/post-1",
        "summary": "<p>AI agent launch summary</p>",
        "id": "guid-1",
        "published": "2026-04-11T08:00:00Z",
    }])
    mocker.patch("nofomo.main.send_messages")

    run_digest(root)

    report = json.loads((root / "data" / "reports" / "2026-04-11.json").read_text(encoding="utf-8"))
    seen_items = json.loads((root / "data" / "seen_items.json").read_text(encoding="utf-8"))

    assert report["total_new_items"] == 1
    assert len(seen_items) == 1


def test_main_dispatches_sync_feedback_command(mocker, tmp_path: Path):
    sync_feedback = mocker.patch("nofomo.main.sync_feedback")
    mocker.patch("sys.argv", ["nofomo", "sync-feedback", "--root", str(tmp_path)])

    main()

    sync_feedback.assert_called_once_with(tmp_path.resolve())


def test_run_digest_marks_bozo_feed_as_failed_source(mocker, tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "data").mkdir()
    (root / "config" / "sources.yaml").write_text(
        "sources:\n  - id: source-a\n    platform: x\n    name: X User\n    rss_url: https://example.com/feed.xml\n",
        encoding="utf-8",
    )
    (root / "config" / "keywords.yaml").write_text("keywords:\n  - agent\n", encoding="utf-8")
    (root / "config" / "telegram.yaml").write_text("bot_token: token123\nchat_id: chat456\n", encoding="utf-8")

    class BrokenFeed:
        bozo = True
        bozo_exception = ValueError("broken feed")
        entries = []

    mocker.patch("nofomo.rss_fetcher.feedparser.parse", return_value=BrokenFeed())
    mocker.patch("nofomo.main.datetime").now.return_value = datetime(2026, 4, 11, 9, 0, tzinfo=UTC)
    send_messages = mocker.patch("nofomo.main.send_messages")

    run_digest(root)

    report = json.loads((root / "data" / "reports" / "2026-04-11.json").read_text(encoding="utf-8"))
    assert report["failed_sources"] == ["source-a"]
    send_messages.assert_called_once()
