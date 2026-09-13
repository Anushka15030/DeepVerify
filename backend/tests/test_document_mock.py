import pytest

from app.providers.document.mock import MockDocumentRetrievalProvider


@pytest.mark.asyncio
async def test_mock_document_search_returns_result() -> None:
    provider = MockDocumentRetrievalProvider()

    response = await provider.search(
        "AI fact checking",
        max_results=5,
    )

    assert response.query == "AI fact checking"
    assert len(response.results) == 1

    result = response.results[0]

    assert result.document_id == "mock-document-001"
    assert result.document_name == "mock-research-paper.pdf"
    assert result.page_number == 3
    assert result.provider == "mock"
    assert result.excerpt


@pytest.mark.asyncio
async def test_mock_document_search_empty_query_returns_no_results() -> None:
    provider = MockDocumentRetrievalProvider()

    response = await provider.search("")

    assert response.results == []


@pytest.mark.asyncio
async def test_mock_document_search_respects_max_results() -> None:
    provider = MockDocumentRetrievalProvider()

    response = await provider.search(
        "AI",
        max_results=1,
    )

    assert len(response.results) <= 1