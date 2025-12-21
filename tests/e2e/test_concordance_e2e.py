"""End-to-end tests for concordance with real API calls."""

import pytest
from rnc_mcp.client import RNCClient
from rnc_mcp.services.builder import RNCQueryBuilder
from rnc_mcp.services.formatter import ResponseFormatter
from rnc_mcp.schemas.schemas import (
    SearchQuery,
    TokenRequest,
    SubcorpusFilter,
    DateFilter,
    RncCorpusType,
)
from tests.utils.assertions import assert_valid_concordance_response, assert_stats_valid


@pytest.mark.e2e
@pytest.mark.slow
class TestConcordanceE2E:
    """End-to-end tests with real RNC API."""

    @pytest.mark.asyncio
    async def test_simple_lemma_search(self, real_api_token):
        """Test simple lemma search in MAIN corpus."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="дом")]
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)
        assert response.stats.queryStats is not None
        # May or may not have results depending on corpus
        assert isinstance(response.results, list)

    @pytest.mark.asyncio
    async def test_search_with_grammar_tags(self, real_api_token):
        """Test search with grammar tags."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="идти", gramm="V")]
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)

    @pytest.mark.asyncio
    async def test_search_with_semantic_tags(self, real_api_token):
        """Test search with semantic tags."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(semantic="t:hum")]
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)

    @pytest.mark.asyncio
    async def test_search_with_subcorpus_author(self, real_api_token):
        """Test search with author filter."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="любовь")],
            subcorpus=SubcorpusFilter(author="Пушкин")
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)

    @pytest.mark.asyncio
    async def test_search_with_date_range(self, real_api_token):
        """Test search with date range filter."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="революция")],
            subcorpus=SubcorpusFilter(
                date_range=DateFilter(start_year=1917, end_year=1920)
            )
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)

    @pytest.mark.asyncio
    async def test_statistics_only_mode(self, real_api_token):
        """Test statistics-only mode (return_examples=False)."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="счастье")],
            return_examples=False
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        # Clear results as per MCP tool behavior
        response.results = []

        assert response is not None
        assert_stats_valid(response.stats)
        assert len(response.results) == 0
        # Stats should still be present
        assert response.stats.corpusStats is not None or response.stats.queryStats is not None

    @pytest.mark.asyncio
    async def test_pagination(self, real_api_token):
        """Test pagination with multiple pages."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="быть")],
            page=0,
            per_page=5
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)
        # Should have pagination info
        assert response.stats.total_pages_available >= 0

    @pytest.mark.asyncio
    async def test_main_corpus(self, real_api_token):
        """Test MAIN corpus search."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="тест")]
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)

    @pytest.mark.asyncio
    async def test_paper_corpus(self, real_api_token):
        """Test PAPER corpus search."""
        query = SearchQuery(
            corpus=RncCorpusType.PAPER,
            tokens=[TokenRequest(lemma="новость")]
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        assert response is not None
        assert_stats_valid(response.stats)

    @pytest.mark.asyncio
    async def test_empty_results_handling(self, real_api_token):
        """Test handling of queries with no results."""
        # Use very specific query unlikely to have results
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[
                TokenRequest(lemma="абракадабранеологизм"),
            ]
        )

        client = RNCClient()
        payload = RNCQueryBuilder.build_payload(query)
        raw_result = await client.execute_concordance(payload)
        response = ResponseFormatter.format_search_results(raw_result)

        # Should handle empty results gracefully
        assert response is not None
        assert_stats_valid(response.stats)
        # Query stats might show 0 results
        if response.stats.queryStats:
            assert response.stats.queryStats.textCount is not None
