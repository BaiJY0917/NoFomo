import json
from pathlib import Path

from nofomo.main import sync_feedback


def test_sync_feedback_appends_valid_feedback_and_advances_offset(mocker, tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "data" / "reports").mkdir(parents=True)
    (root / "config" / "telegram.yaml").write_text("bot_token: token123\nchat_id: chat456\n", encoding="utf-8")
    (root / "data" / "reports" / "2026-04-11.json").write_text(
        json.dumps({
            "report_date": "2026-04-11",
            "generated_at": "2026-04-11T09:00:00Z",
            "total_new_items": 1,
            "total_sources": 1,
            "total_highlights": 1,
            "failed_sources": [],
            "highlights": [{
                "item_id": "item-1",
                "source_id": "source-a",
                "source_name": "X User",
                "matched_keywords": ["agent"],
            }],
            "normal_items": [],
        }),
        encoding="utf-8",
    )
    mocker.patch("nofomo.main.fetch_updates", return_value=[{
        "update_id": 101,
        "message": {
            "message_id": 9,
            "date": 1712822400,
            "text": "/like item-1",
            "from": {"id": 1},
            "chat": {"id": 2},
        },
    }])

    sync_feedback(root)

    lines = (root / "data" / "feedback.jsonl").read_text(encoding="utf-8").splitlines()
    state = json.loads((root / "data" / "telegram_state.json").read_text(encoding="utf-8"))

    assert json.loads(lines[0])["item_id"] == "item-1"
    assert state["offset"] == 102
