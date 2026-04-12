import json
from pathlib import Path

from nofomo.models import FeedbackRecord
from nofomo.report_store import append_feedback_record


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
