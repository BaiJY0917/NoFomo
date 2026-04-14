from pathlib import Path

from nofomo.deduper import build_item_id, compute_dedupe_key, filter_new_entries, load_seen_items, save_seen_items


def test_compute_dedupe_key_prefers_url_over_guid():
    entry = {
        "link": "https://example.com/post-1",
        "id": "guid-1",
        "title": "Hello",
        "published": "2026-04-11T08:00:00Z",
    }

    assert compute_dedupe_key("source-a", entry) == "url:https://example.com/post-1"


def test_build_item_id_is_stable_for_same_entry():
    entry = {
        "link": "https://example.com/post-1",
        "id": "guid-1",
        "title": "Hello",
        "published": "2026-04-11T08:00:00Z",
    }

    assert build_item_id("source-a", entry) == build_item_id("source-a", entry)


def test_filter_new_entries_skips_seen_items():
    entries = [
        {"link": "https://example.com/post-1", "title": "One", "published": "2026-04-11"},
        {"link": "https://example.com/post-2", "title": "Two", "published": "2026-04-11"},
    ]

    new_entries = filter_new_entries("source-a", entries, {"url:https://example.com/post-1"})

    assert [entry["title"] for entry in new_entries] == ["Two"]


def test_seen_items_round_trip(tmp_path: Path):
    seen_file = tmp_path / "seen_items.json"

    save_seen_items(seen_file, {"url:https://example.com/post-1"})

    assert load_seen_items(seen_file) == {"url:https://example.com/post-1"}
