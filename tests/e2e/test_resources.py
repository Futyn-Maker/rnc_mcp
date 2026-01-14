"""E2E tests for resource generation.

Tests verify that resources are generated correctly for all corpus types.
Only validates that valid Markdown is returned, not specific content.
"""

import pytest
from tests.fixtures.e2e_queries import ALL_CORPUS_TYPES


@pytest.mark.e2e
@pytest.mark.asyncio
class TestResourceGeneration:
    """Test resource generation for all corpus types."""

    @pytest.mark.parametrize("corpus", ALL_CORPUS_TYPES)
    async def test_corpus_info_resource(self, mcp_client, corpus):
        """Each corpus should have a valid info resource returning Markdown."""
        resource_uri = f"rnc://{corpus}/info"

        async with mcp_client() as client:
            result = await client.read_resource(resource_uri)

        # Result should be a list with at least one element
        assert result is not None
        assert len(result) > 0

        # Get the resource content
        resource = result[0]
        content = resource.text

        # Should be non-empty Markdown
        assert content is not None
        assert len(content) > 0

        # Basic Markdown validation - should contain headers or formatted text
        assert isinstance(content, str)

    async def test_list_resources(self, mcp_client):
        """Server should list all available resources."""
        async with mcp_client() as client:
            resources = await client.list_resources()

        # Should have resources for all corpus types
        assert len(resources) >= len(ALL_CORPUS_TYPES)

        # Verify resource URIs follow expected pattern
        resource_uris = [str(r.uri) for r in resources]
        for corpus in ALL_CORPUS_TYPES:
            expected_uri = f"rnc://{corpus}/info"
            assert expected_uri in resource_uris, f"Missing resource: {corpus}"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestResourceContent:
    """Test resource content structure."""

    async def test_main_corpus_resource_has_content(self, mcp_client):
        """MAIN corpus resource should have meaningful content."""
        async with mcp_client() as client:
            result = await client.read_resource("rnc://MAIN/info")

        resource = result[0]
        content = resource.text

        # Should have substantial content
        assert len(content) > 100, "Resource content seems too short"

    async def test_poetic_corpus_resource(self, mcp_client):
        """POETIC corpus resource should be accessible."""
        async with mcp_client() as client:
            result = await client.read_resource("rnc://POETIC/info")

        resource = result[0]
        content = resource.text

        assert len(content) > 0


@pytest.mark.e2e
@pytest.mark.asyncio
class TestServerCapabilities:
    """Test server capabilities and tool discovery."""

    async def test_list_tools(self, mcp_client):
        """Server should list the concordance tool."""
        async with mcp_client() as client:
            tools = await client.list_tools()

        # Should have at least the concordance tool
        assert len(tools) >= 1

        tool_names = [t.name for t in tools]
        assert "concordance" in tool_names

    async def test_concordance_tool_has_description(self, mcp_client):
        """Concordance tool should have a description."""
        async with mcp_client() as client:
            tools = await client.list_tools()

        concordance_tool = next(t for t in tools if t.name == "concordance")
        assert concordance_tool.description is not None
        assert len(concordance_tool.description) > 0

    async def test_server_ping(self, mcp_client):
        """Server should respond to ping."""
        async with mcp_client() as client:
            await client.ping()
