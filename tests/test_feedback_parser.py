import json
from pathlib import Path

from nofomo.models import FeedbackRecord
from nofomo.report_store import append_feedback_record
from nofomo.telegram_feedback import extract_feedback_command, load_offset, next_offset, save_offset


def test_append_feedback_record_writes_json_line(tmp_path: Path):
    record = FeedbackRecord(
        item_id="item-1",
        report_date="2026-04-11",
        feedback_type="like",
        source_id="source-a",
        source_name="X User",
        matched_keywords=["agent"],
        telegram_user_id=1,
        telegram_chat_id=2,
        telegram_message_id=3,
        created_at="2026-04-11T10:00:00Z",
    )

    append_feedback_record(tmp_path / "feedback.jsonl", record)

    lines = (tmp_path / "feedback.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["feedback_type"] == "like"


def test_extract_feedback_command_parses_like_command():
    update = {
        "update_id": 101,
        "message": {
            "message_id": 9,
            "date": 1712822400,
            "text": "/like item-1",
            "from": {"id": 1},
            "chat": {"id": 2},
        },
    }

    parsed = extract_feedback_command(update)

    assert parsed is not None
    assert parsed["feedback_type"] == "like"
    assert parsed["item_id"] == "item-1"


def test_extract_feedback_command_ignores_invalid_message():
    update = {"update_id": 102, "message": {"text": "hello"}}

    assert extract_feedback_command(update) is None


def test_extract_feedback_command_returns_none_when_required_fields_are_missing():
    update = {
        "update_id": 103,
        "message": {
            "text": "/like item-1",
        },
    }

    assert extract_feedback_command(update) is None


def test_offset_round_trip(tmp_path: Path):
    path = tmp_path / "telegram_state.json"

    save_offset(path, 105)

    assert load_offset(path) == 105
    assert next_offset(105) == 106
