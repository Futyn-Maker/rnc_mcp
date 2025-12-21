"""Integration tests for RNCClient with mocked HTTP."""

import pytest
import respx
import httpx
from rnc_mcp.client import RNCClient
from rnc_mcp.config import Config
from tests.fixtures.mock_responses import (
    CONCORDANCE_SUCCESS,
    CORPUS_CONFIG_MAIN,
    ATTRIBUTES_GRAMMAR,
    ERROR_401_RESPONSE,
)


@pytest.mark.integration
class TestConcordanceExecution:
    """Tests for execute_concordance method."""

    @pytest.mark.asyncio
    async def test_success_response(self, mock_env_token):
        """Test successful concordance execution."""
        client = RNCClient()
        payload = {"corpus": {"type": "MAIN"}, "lexGramm": [], "params": {}}

        with respx.mock:
            route = respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(return_value=httpx.Response(200, json=CONCORDANCE_SUCCESS))

            result = await client.execute_concordance(payload)

            assert route.called
            assert result == CONCORDANCE_SUCCESS

    @pytest.mark.asyncio
    async def test_includes_authorization_header(self, mock_env_token):
        """Test that Authorization header is included."""
        client = RNCClient()
        payload = {"test": "data"}

        with respx.mock:
            route = respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.execute_concordance(payload)

            assert route.called
            request = route.calls.last.request
            assert "Authorization" in request.headers
            assert request.headers["Authorization"] == f"Bearer {mock_env_token}"

    @pytest.mark.asyncio
    async def test_posts_to_correct_endpoint(self, mock_env_token):
        """Test that POST request goes to correct endpoint."""
        client = RNCClient()
        payload = {}

        with respx.mock:
            route = respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.execute_concordance(payload)

            assert route.called
            assert route.calls.last.request.method == "POST"

    @pytest.mark.asyncio
    async def test_401_unauthorized_raises_value_error(self, mock_env_token):
        """Test that 401 Unauthorized raises ValueError with specific message."""
        client = RNCClient()
        payload = {}

        with respx.mock:
            respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(return_value=httpx.Response(401, json=ERROR_401_RESPONSE))

            with pytest.raises(ValueError) as exc_info:
                await client.execute_concordance(payload)

            assert "Invalid RNC Token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_404_raises_value_error_with_status(self, mock_env_token):
        """Test that 404 raises ValueError with status code."""
        client = RNCClient()
        payload = {}

        with respx.mock:
            respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(return_value=httpx.Response(404, json={"detail": "Not found"}))

            with pytest.raises(ValueError) as exc_info:
                await client.execute_concordance(payload)

            assert "404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_500_server_error_raises_value_error(self, mock_env_token):
        """Test that 500 Server Error raises ValueError."""
        client = RNCClient()
        payload = {}

        with respx.mock:
            respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(return_value=httpx.Response(500, text="Internal Server Error"))

            with pytest.raises(ValueError) as exc_info:
                await client.execute_concordance(payload)

            assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_raises_timeout_exception(self, mock_env_token):
        """Test that timeout raises appropriate exception."""
        client = RNCClient()
        payload = {}

        with respx.mock:
            respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(side_effect=httpx.TimeoutException("Request timeout"))

            with pytest.raises(httpx.TimeoutException):
                await client.execute_concordance(payload)

    @pytest.mark.asyncio
    async def test_network_error_raises_exception(self, mock_env_token):
        """Test that network errors raise appropriate exception."""
        client = RNCClient()
        payload = {}

        with respx.mock:
            respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(side_effect=httpx.ConnectError("Connection failed"))

            with pytest.raises(httpx.ConnectError):
                await client.execute_concordance(payload)

    @pytest.mark.asyncio
    async def test_malformed_json_raises_exception(self, mock_env_token):
        """Test that malformed JSON response raises exception."""
        client = RNCClient()
        payload = {}

        with respx.mock:
            respx.post(
                f"{Config.BASE_URL}/lex-gramm/concordance"
            ).mock(return_value=httpx.Response(200, text="Not JSON"))

            with pytest.raises(Exception):  # JSONDecodeError
                await client.execute_concordance(payload)


@pytest.mark.integration
class TestCorpusConfig:
    """Tests for get_corpus_config method."""

    @pytest.mark.asyncio
    async def test_success_response(self, mock_env_token):
        """Test successful corpus config retrieval."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(return_value=httpx.Response(200, json=CORPUS_CONFIG_MAIN))

            result = await client.get_corpus_config("MAIN")

            assert route.called
            assert result == CORPUS_CONFIG_MAIN

    @pytest.mark.asyncio
    async def test_correct_endpoint(self, mock_env_token):
        """Test that GET request goes to /config/ endpoint."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_corpus_config("MAIN")

            assert route.called
            assert route.calls.last.request.method == "GET"

    @pytest.mark.asyncio
    async def test_includes_corpus_param(self, mock_env_token):
        """Test that corpus param is included correctly."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_corpus_config("MAIN")

            assert route.called
            request = route.calls.last.request
            # Check query params contain corpus
            assert "corpus" in str(request.url)

    @pytest.mark.asyncio
    async def test_main_corpus_type(self, mock_env_token):
        """Test getting config for MAIN corpus."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(return_value=httpx.Response(200, json=CORPUS_CONFIG_MAIN))

            result = await client.get_corpus_config("MAIN")

            assert route.called
            assert "sortings" in result

    @pytest.mark.asyncio
    async def test_paper_corpus_type(self, mock_env_token):
        """Test getting config for PAPER corpus."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(return_value=httpx.Response(200, json=CORPUS_CONFIG_MAIN))

            result = await client.get_corpus_config("PAPER")

            assert route.called

    @pytest.mark.asyncio
    async def test_401_unauthorized(self, mock_env_token):
        """Test 401 handling for corpus config."""
        client = RNCClient()

        with respx.mock:
            respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(return_value=httpx.Response(401, json=ERROR_401_RESPONSE))

            with pytest.raises(Exception):  # Will raise HTTPStatusError
                await client.get_corpus_config("MAIN")

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_env_token):
        """Test timeout handling for corpus config."""
        client = RNCClient()

        with respx.mock:
            respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(httpx.TimeoutException):
                await client.get_corpus_config("MAIN")

    @pytest.mark.asyncio
    async def test_includes_auth_header(self, mock_env_token):
        """Test that auth header is included."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/config/"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_corpus_config("MAIN")

            request = route.calls.last.request
            assert "Authorization" in request.headers


@pytest.mark.integration
class TestAttributes:
    """Tests for get_attributes method."""

    @pytest.mark.asyncio
    async def test_grammar_attributes(self, mock_env_token):
        """Test getting grammar attributes."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/attrs/gr"
            ).mock(return_value=httpx.Response(200, json=ATTRIBUTES_GRAMMAR))

            result = await client.get_attributes("MAIN", "gr")

            assert route.called
            assert result == ATTRIBUTES_GRAMMAR

    @pytest.mark.asyncio
    async def test_semantic_attributes_endpoint(self, mock_env_token):
        """Test semantic attributes endpoint."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/attrs/sem"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_attributes("MAIN", "sem")

            assert route.called
            assert "/attrs/sem" in str(route.calls.last.request.url)

    @pytest.mark.asyncio
    async def test_syntax_attributes_endpoint(self, mock_env_token):
        """Test syntax attributes endpoint."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/attrs/syntax"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_attributes("MAIN", "syntax")

            assert route.called
            assert "/attrs/syntax" in str(route.calls.last.request.url)

    @pytest.mark.asyncio
    async def test_flags_attributes_endpoint(self, mock_env_token):
        """Test flags attributes endpoint."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/attrs/flags"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_attributes("MAIN", "flags")

            assert route.called
            assert "/attrs/flags" in str(route.calls.last.request.url)

    @pytest.mark.asyncio
    async def test_includes_corpus_param(self, mock_env_token):
        """Test that corpus param is included."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/attrs/gr"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_attributes("PAPER", "gr")

            assert route.called
            # Corpus should be in query params
            assert "corpus" in str(route.calls.last.request.url)

    @pytest.mark.asyncio
    async def test_401_handling(self, mock_env_token):
        """Test 401 handling for attributes."""
        client = RNCClient()

        with respx.mock:
            respx.get(
                f"{Config.BASE_URL}/attrs/gr"
            ).mock(return_value=httpx.Response(401, json=ERROR_401_RESPONSE))

            with pytest.raises(Exception):  # Will raise HTTPStatusError
                await client.get_attributes("MAIN", "gr")

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_env_token):
        """Test timeout handling for attributes."""
        client = RNCClient()

        with respx.mock:
            respx.get(
                f"{Config.BASE_URL}/attrs/gr"
            ).mock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(httpx.TimeoutException):
                await client.get_attributes("MAIN", "gr")

    @pytest.mark.asyncio
    async def test_correct_auth_header(self, mock_env_token):
        """Test that correct auth header is sent."""
        client = RNCClient()

        with respx.mock:
            route = respx.get(
                f"{Config.BASE_URL}/attrs/gr"
            ).mock(return_value=httpx.Response(200, json={}))

            await client.get_attributes("MAIN", "gr")

            request = route.calls.last.request
            assert "Authorization" in request.headers
            assert request.headers["Authorization"] == f"Bearer {mock_env_token}"
