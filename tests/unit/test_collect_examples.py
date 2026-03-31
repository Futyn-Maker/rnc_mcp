"""Unit tests for multi-page example collection."""

import pytest
from unittest.mock import AsyncMock, Mock

from rnc_mcp.schemas.schemas import (
    SearchQuery, TokenRequest, RncCorpusType,
)
from rnc_mcp.mcp import _collect_examples
from tests.fixtures.mock_responses import (
    make_multipage_response,
)


@pytest.fixture
def mock_ctx():
    """Mock FastMCP Context with async logging methods."""
    ctx = Mock()
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    return ctx


@pytest.fixture
def mock_client():
    """Mock RNCClient with AsyncMock execute_concordance."""
    client = Mock()
    client.execute_concordance = AsyncMock()
    return client


def _query(max_examples, page=0):
    """Helper to create a SearchQuery with max_examples."""
    return SearchQuery(
        corpus=RncCorpusType.MAIN,
        tokens=[TokenRequest(lemma="тест")],
        page=page,
        max_examples=max_examples,
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestCollectExamplesBasic:
    """Basic multi-page collection tests."""

    async def test_single_page_sufficient(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Stop after one page when enough examples."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        # 2 docs * 2 snippets = 4 examples per page
        mock_client.execute_concordance.return_value = (
            make_multipage_response(
                page=0, total_pages=5,
                docs_per_page=2, snippets_per_doc=2,
            )
        )

        result = await _collect_examples(
            _query(max_examples=4), mock_client, mock_ctx
        )

        assert mock_client.execute_concordance.call_count == 1
        total = sum(
            len(d.examples) for d in result.results
        )
        assert total == 4
        assert result.stats.last_page_fetched == 0

    async def test_multi_page_collection(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Fetch multiple pages to reach max_examples."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        # 2 docs * 2 snippets = 4 examples per page
        # Need 10 examples => 3 pages (4+4+2)
        def side_effect(payload, **kwargs):
            pg = payload["params"]["pageParams"]["page"]
            return make_multipage_response(
                page=pg, total_pages=10,
                docs_per_page=2, snippets_per_doc=2,
            )

        mock_client.execute_concordance.side_effect = (
            side_effect
        )

        result = await _collect_examples(
            _query(max_examples=10), mock_client, mock_ctx
        )

        assert mock_client.execute_concordance.call_count == 3
        total = sum(
            len(d.examples) for d in result.results
        )
        assert total == 10
        assert result.stats.last_page_fetched == 2

    async def test_start_from_nonzero_page(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Respect starting page parameter."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        def side_effect(payload, **kwargs):
            pg = payload["params"]["pageParams"]["page"]
            return make_multipage_response(
                page=pg, total_pages=10,
                docs_per_page=2, snippets_per_doc=2,
            )

        mock_client.execute_concordance.side_effect = (
            side_effect
        )

        result = await _collect_examples(
            _query(max_examples=4, page=3),
            mock_client, mock_ctx,
        )

        # Should start from page 3
        first_call_payload = (
            mock_client.execute_concordance
            .call_args_list[0][0][0]
        )
        assert (
            first_call_payload["params"]["pageParams"]["page"]
            == 3
        )
        assert result.stats.last_page_fetched == 3


@pytest.mark.unit
@pytest.mark.asyncio
class TestCollectExamplesTrimming:
    """Tests for example trimming at boundaries."""

    async def test_trims_excess_examples(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Trim examples in last doc to not exceed max."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        # 2 docs * 3 snippets = 6 per page, want 5
        mock_client.execute_concordance.return_value = (
            make_multipage_response(
                page=0, total_pages=5,
                docs_per_page=2, snippets_per_doc=3,
            )
        )

        result = await _collect_examples(
            _query(max_examples=5), mock_client, mock_ctx
        )

        total = sum(
            len(d.examples) for d in result.results
        )
        assert total == 5
        # First doc has 3, second trimmed to 2
        assert len(result.results[0].examples) == 3
        assert len(result.results[1].examples) == 2

    async def test_stops_at_exact_boundary(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """No trimming needed when examples match exactly."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        # 2 docs * 2 snippets = 4 per page, want 4
        mock_client.execute_concordance.return_value = (
            make_multipage_response(
                page=0, total_pages=5,
                docs_per_page=2, snippets_per_doc=2,
            )
        )

        result = await _collect_examples(
            _query(max_examples=4), mock_client, mock_ctx
        )

        total = sum(
            len(d.examples) for d in result.results
        )
        assert total == 4
        assert mock_client.execute_concordance.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestCollectExamplesExhaustion:
    """Tests for when results are exhausted."""

    async def test_stops_at_last_page(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Stop when all pages are exhausted."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        # 3 pages * 2 docs * 1 snippet = 6 total
        # Asking for 100, but only 6 exist
        def side_effect(payload, **kwargs):
            pg = payload["params"]["pageParams"]["page"]
            return make_multipage_response(
                page=pg, total_pages=3,
                docs_per_page=2, snippets_per_doc=1,
            )

        mock_client.execute_concordance.side_effect = (
            side_effect
        )

        result = await _collect_examples(
            _query(max_examples=100), mock_client, mock_ctx
        )

        assert mock_client.execute_concordance.call_count == 3
        total = sum(
            len(d.examples) for d in result.results
        )
        assert total == 6
        assert result.stats.last_page_fetched == 2


@pytest.mark.unit
@pytest.mark.asyncio
class TestCollectExamplesRetry:
    """Tests for retry logic on failures."""

    async def test_retry_then_success(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Retry a failed request and continue."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        page0 = make_multipage_response(
            page=0, total_pages=5,
            docs_per_page=2, snippets_per_doc=2,
        )

        # Fail once on page 1, then succeed
        call_count = {"n": 0}

        async def side_effect(payload, **kwargs):
            call_count["n"] += 1
            pg = payload["params"]["pageParams"]["page"]
            if pg == 1 and call_count["n"] == 2:
                raise RuntimeError("Temporary failure")
            return make_multipage_response(
                page=pg, total_pages=5,
                docs_per_page=2, snippets_per_doc=2,
            )

        mock_client.execute_concordance.side_effect = (
            side_effect
        )

        result = await _collect_examples(
            _query(max_examples=8), mock_client, mock_ctx
        )

        # page 0 ok, page 1 fail, page 1 retry ok
        assert mock_client.execute_concordance.call_count == 3
        total = sum(
            len(d.examples) for d in result.results
        )
        assert total == 8

    async def test_three_consecutive_failures_returns_partial(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Return partial results after 3 consecutive fails."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0
        Config.RNC_MAX_RETRIES = 3

        call_count = {"n": 0}

        async def side_effect(payload, **kwargs):
            call_count["n"] += 1
            pg = payload["params"]["pageParams"]["page"]
            if pg >= 1:
                raise RuntimeError("Server error")
            return make_multipage_response(
                page=pg, total_pages=10,
                docs_per_page=2, snippets_per_doc=2,
            )

        mock_client.execute_concordance.side_effect = (
            side_effect
        )

        result = await _collect_examples(
            _query(max_examples=100), mock_client, mock_ctx
        )

        # page 0 ok (1 call), page 1 fails 3 times
        assert mock_client.execute_concordance.call_count == 4
        total = sum(
            len(d.examples) for d in result.results
        )
        assert total == 4  # only page 0 results
        assert result.stats.last_page_fetched == 0

    async def test_all_requests_fail_raises_error(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Raise RuntimeError when no data is collected."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0
        Config.RNC_MAX_RETRIES = 3

        mock_client.execute_concordance.side_effect = (
            RuntimeError("Always fails")
        )

        with pytest.raises(RuntimeError, match="Failed"):
            await _collect_examples(
                _query(max_examples=10),
                mock_client, mock_ctx,
            )


@pytest.mark.unit
@pytest.mark.asyncio
class TestCollectExamplesPayload:
    """Tests for payload overrides."""

    async def test_overrides_docs_per_page(
        self, mock_client, mock_ctx, monkeypatch
    ):
        """Ensure docsPerPage is overridden to 50."""
        monkeypatch.setenv("RNC_API_TOKEN", "tok")
        from rnc_mcp.config import Config
        Config._RNC_TOKEN = "tok"
        Config.RNC_PAGE_DELAY = 0

        mock_client.execute_concordance.return_value = (
            make_multipage_response(
                page=0, total_pages=1,
                docs_per_page=1, snippets_per_doc=1,
            )
        )

        await _collect_examples(
            _query(max_examples=1), mock_client, mock_ctx
        )

        payload = (
            mock_client.execute_concordance
            .call_args[0][0]
        )
        page_params = payload["params"]["pageParams"]
        assert page_params["docsPerPage"] == 50
        assert page_params["snippetsPerDoc"] == 10
