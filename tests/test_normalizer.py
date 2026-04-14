from nofomo.normalizer import normalize_entry


def test_normalize_entry_strips_html_and_keeps_title():
    entry = {
        "title": "Hello World",
        "link": "https://example.com/post-1",
        "summary": "<p>AI <b>agent</b> update</p>",
        "id": "guid-1",
        "published": "2026-04-11T08:00:00Z",
    }

    item = normalize_entry(
        source_id="source-a",
        platform="x",
        source_name="X User",
        item_id="abc123def456",
        entry=entry,
    )

    assert item.title == "Hello World"
    assert item.raw_summary == "<p>AI <b>agent</b> update</p>"
    assert item.normalized_text == "AI agent update"
