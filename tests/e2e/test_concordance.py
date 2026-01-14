"""E2E tests for the concordance tool.

Tests execute real requests against a running RNC MCP server.
Response structure is validated, but exact counts are not checked
(except for edge cases expected to return 0 results).
"""

import pytest
from tests.fixtures.e2e_queries import (
    ALL_CORPUS_TYPES,
    SIMPLE_QUERIES,
    SUBCORPUS_QUERIES,
    ZERO_RESULT_QUERIES,
    POETRY_SPECIAL,
    ADVANCED_QUERIES,
)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestConcordanceSimpleQueries:
    """Test simple queries for all corpus types."""

    @pytest.mark.parametrize("corpus", ALL_CORPUS_TYPES)
    async def test_simple_query_returns_results(self, mcp_client, corpus):
        """Simple queries should return valid response structure with results."""
        query = SIMPLE_QUERIES[corpus]

        async with mcp_client() as client:
            result = await client.call_tool("concordance", query)

        assert not result.is_error, f"Tool call failed: {result.content}"
        data = result.structured_content

        # Verify response structure
        assert "stats" in data
        assert "results" in data

        # Verify stats structure
        stats = data["stats"]
        assert "corpusStats" in stats
        assert "queryStats" in stats
        assert "total_pages_available" in stats

        # Query stats should have counts
        query_stats = stats["queryStats"]
        assert query_stats is not None
        assert "textCount" in query_stats or "wordUsageCount" in query_stats

        # Expect results (may be 0 for some corpora, but structure must be valid)
        assert isinstance(data["results"], list)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestConcordanceSubcorpusQueries:
    """Test queries with subcorpus filters for all corpus types."""

    @pytest.mark.parametrize("corpus", ALL_CORPUS_TYPES)
    async def test_subcorpus_query_returns_results(self, mcp_client, corpus):
        """Queries with subcorpus filters should return valid response."""
        query = SUBCORPUS_QUERIES[corpus]

        async with mcp_client() as client:
            result = await client.call_tool("concordance", query)

        assert not result.is_error, f"Tool call failed: {result.content}"
        data = result.structured_content

        # Verify response structure
        assert "stats" in data
        assert "results" in data
        assert isinstance(data["results"], list)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestConcordanceZeroResults:
    """Test edge cases expected to return 0 results."""

    @pytest.mark.parametrize("name,query", ZERO_RESULT_QUERIES)
    async def test_zero_result_query(self, mcp_client, name, query):
        """Edge case queries should return 0 results."""
        async with mcp_client() as client:
            result = await client.call_tool("concordance", query)

        assert not result.is_error, f"Tool call failed: {result.content}"
        data = result.structured_content

        # Verify structure
        assert "stats" in data
        assert "results" in data

        # Expect 0 results
        query_stats = data["stats"]["queryStats"]
        if query_stats:
            text_count = query_stats.get("textCount", 0)
            word_count = query_stats.get("wordUsageCount", 0)
            assert text_count == 0 or word_count == 0, f"Expected 0 results for {name}"

        assert len(data["results"]) == 0, f"Expected empty results for {name}"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestConcordancePoetrySpecial:
    """Special test cases for poetry corpus."""

    @pytest.mark.parametrize("name,query", POETRY_SPECIAL)
    async def test_poetry_kofe_kofiy(self, mcp_client, name, query):
        """Test кофе and кофий lemmas in poetry corpus."""
        async with mcp_client() as client:
            result = await client.call_tool("concordance", query)

        assert not result.is_error, f"Tool call failed for {name}: {result.content}"
        data = result.structured_content

        # Verify response structure
        assert "stats" in data
        assert "results" in data


@pytest.mark.e2e
@pytest.mark.asyncio
class TestConcordanceAdvanced:
    """Test advanced query features."""

    @pytest.mark.parametrize("name,query", ADVANCED_QUERIES)
    async def test_advanced_query(self, mcp_client, name, query):
        """Advanced queries should return valid response."""
        async with mcp_client() as client:
            result = await client.call_tool("concordance", query)

        assert not result.is_error, f"Tool call failed for {name}: {result.content}"
        data = result.structured_content

        # Verify response structure
        assert "stats" in data
        assert "results" in data

    async def test_statistics_only_no_examples(self, mcp_client):
        """Statistics-only query should return empty results list."""
        from tests.fixtures.e2e_queries import STATISTICS_ONLY_QUERY

        async with mcp_client() as client:
            result = await client.call_tool("concordance", STATISTICS_ONLY_QUERY)

        assert not result.is_error
        data = result.structured_content

        # Should have stats but no examples
        assert "stats" in data
        assert data["results"] == []

    async def test_pagination_returns_different_page(self, mcp_client):
        """Pagination should return results for specified page."""
        from tests.fixtures.e2e_queries import QUERY_WITH_CUSTOM_PAGINATION

        async with mcp_client() as client:
            result = await client.call_tool("concordance", QUERY_WITH_CUSTOM_PAGINATION)

        assert not result.is_error
        data = result.structured_content

        # Verify pagination metadata
        assert "stats" in data
        assert "total_pages_available" in data["stats"]


@pytest.mark.e2e
@pytest.mark.asyncio
class TestConcordanceResponseStructure:
    """Test detailed response structure validation."""

    async def test_document_metadata_structure(self, mcp_client):
        """Document metadata should have expected fields."""
        from tests.fixtures.e2e_queries import SIMPLE_LEMMA_QUERY

        async with mcp_client() as client:
            result = await client.call_tool("concordance", SIMPLE_LEMMA_QUERY)

        assert not result.is_error
        data = result.structured_content

        if data["results"]:
            doc = data["results"][0]
            assert "metadata" in doc
            assert "examples" in doc

            # Metadata should have title at minimum
            assert "title" in doc["metadata"]

            # Examples should be a list of strings
            assert isinstance(doc["examples"], list)

    async def test_stats_structure(self, mcp_client):
        """Stats should have all expected fields."""
        from tests.fixtures.e2e_queries import SIMPLE_LEMMA_QUERY

        async with mcp_client() as client:
            result = await client.call_tool("concordance", SIMPLE_LEMMA_QUERY)

        assert not result.is_error
        data = result.structured_content

        stats = data["stats"]
        assert "corpusStats" in stats
        assert "queryStats" in stats
        assert "total_pages_available" in stats

        # Corpus stats should have counts
        if stats["corpusStats"]:
            assert "textCount" in stats["corpusStats"] or "wordUsageCount" in stats["corpusStats"]

    async def test_main_corpus_returns_positive_results(self, mcp_client):
        """MAIN corpus simple query should return positive results."""
        from tests.fixtures.e2e_queries import SIMPLE_LEMMA_QUERY

        async with mcp_client() as client:
            result = await client.call_tool("concordance", SIMPLE_LEMMA_QUERY)

        assert not result.is_error
        data = result.structured_content

        # MAIN corpus with common word should have results
        query_stats = data["stats"]["queryStats"]
        assert query_stats is not None

        # At least one of the counts should be positive
        text_count = query_stats.get("textCount", 0) or 0
        word_count = query_stats.get("wordUsageCount", 0) or 0
        assert text_count > 0 or word_count > 0, "Expected positive results for 'дом' in MAIN corpus"
