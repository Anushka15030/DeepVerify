from app.agents.claim_extractor import ClaimExtractor


def test_extracts_factual_sentences():
    extractor = ClaimExtractor()

    text = (
        "Solar capacity increased by 25% in 2025. "
        "India added 12 GW of new capacity."
    )

    claims = extractor.extract(text)

    assert claims == [
        "Solar capacity increased by 25% in 2025.",
        "India added 12 GW of new capacity.",
    ]


def test_ignores_questions():
    extractor = ClaimExtractor()

    text = (
        "India added 12 GW of solar capacity. "
        "Why did solar capacity increase?"
    )

    claims = extractor.extract(text)

    assert claims == [
        "India added 12 GW of solar capacity.",
    ]


def test_empty_text_returns_no_claims():
    extractor = ClaimExtractor()

    assert extractor.extract("") == []


def test_ignores_short_fragments():
    extractor = ClaimExtractor()

    text = "Conclusion. Solar capacity increased significantly in 2025."

    claims = extractor.extract(text)

    assert claims == [
        "Solar capacity increased significantly in 2025.",
    ]