from nofomo.summarizer import build_summaries


def test_build_summaries_prefers_existing_summary_text():
    short_text, long_text = build_summaries(
        raw_summary="<p>AI agent weekly recap with product launch details.</p>",
        normalized_text="AI agent weekly recap with product launch details.",
    )

    assert short_text == "AI agent weekly recap with product launch details."
    assert long_text == "AI agent weekly recap with product launch details."


def test_build_summaries_falls_back_to_trimmed_body_text():
    short_text, long_text = build_summaries(raw_summary="", normalized_text="One two three four five six seven eight nine ten eleven twelve")

    assert short_text.startswith("One two three")
    assert len(short_text) <= 120
    assert len(long_text) <= 280
