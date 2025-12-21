"""Custom assertion helpers for RNC MCP tests."""

from rnc_mcp.schemas.schemas import ConcordanceResponse, GlobalStats


def assert_valid_concordance_response(response: ConcordanceResponse):
    """Assert response matches ConcordanceResponse schema."""
    assert response is not None
    assert hasattr(response, 'stats')
    assert hasattr(response, 'results')

    # Stats should be present
    assert response.stats is not None
    assert response.stats.total_pages_available >= 0

    # Results should be a list
    assert isinstance(response.results, list)

    # Each document in results should have metadata and examples
    for doc in response.results:
        assert doc.metadata is not None
        assert doc.metadata.title is not None
        assert isinstance(doc.examples, list)
        assert len(doc.examples) > 0


def assert_payload_structure(payload: dict):
    """Assert payload matches RNC API requirements."""
    assert "corpus" in payload
    assert "type" in payload["corpus"]

    assert "lexGramm" in payload
    assert isinstance(payload["lexGramm"], list)

    assert "params" in payload
    assert "pageParams" in payload["params"]
    assert "globalConditions" in payload["params"]


def assert_has_auth_header(headers: dict):
    """Assert headers include valid authorization."""
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")
    assert len(headers["Authorization"]) > len("Bearer ")


def assert_markdown_format(text: str):
    """Assert text is valid markdown."""
    assert isinstance(text, str)
    assert len(text) > 0
    # Basic markdown checks - should have headers or lists
    assert "#" in text or "-" in text or "*" in text


def assert_stats_valid(stats: GlobalStats):
    """Assert GlobalStats structure is valid."""
    assert stats is not None
    assert hasattr(stats, 'total_pages_available')
    assert stats.total_pages_available >= 0

    # Stats fields can be None
    if stats.corpusStats is not None:
        assert hasattr(stats.corpusStats, 'textCount')
        assert hasattr(stats.corpusStats, 'wordUsageCount')

    if stats.subcorpStats is not None:
        assert hasattr(stats.subcorpStats, 'textCount')
        assert hasattr(stats.subcorpStats, 'wordUsageCount')

    if stats.queryStats is not None:
        assert hasattr(stats.queryStats, 'textCount')
        assert hasattr(stats.queryStats, 'wordUsageCount')
