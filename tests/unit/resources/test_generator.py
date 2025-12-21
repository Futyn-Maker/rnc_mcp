"""Unit tests for CorpusResourceGenerator."""

import pytest
from unittest.mock import AsyncMock
from rnc_mcp.resources.generator import CorpusResourceGenerator
from tests.fixtures.mock_responses import (
    CORPUS_CONFIG_MAIN,
    CORPUS_CONFIG_NO_SORTINGS,
    ATTRIBUTES_GRAMMAR,
    ATTRIBUTES_EMPTY,
)


@pytest.mark.unit
class TestMarkdownGeneration:
    """Tests for markdown generation."""

    @pytest.mark.asyncio
    async def test_valid_corpus_generates_markdown(
            self, mock_rnc_client, mock_env_token):
        """Test that valid corpus generates full markdown."""
        mock_rnc_client.get_corpus_config.return_value = CORPUS_CONFIG_MAIN
        mock_rnc_client.get_attributes.return_value = ATTRIBUTES_GRAMMAR

        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "# Configuration for MAIN" in result

    @pytest.mark.asyncio
    async def test_sorting_methods_section(
            self, mock_rnc_client, mock_env_token):
        """Test sorting methods section formatting."""
        mock_rnc_client.get_corpus_config.return_value = CORPUS_CONFIG_MAIN
        mock_rnc_client.get_attributes.return_value = ATTRIBUTES_EMPTY

        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        assert "## Available Sorting Methods" in result
        assert "grcreated" in result

    @pytest.mark.asyncio
    async def test_no_sorting_methods_section_skipped(
            self, mock_rnc_client, mock_env_token):
        """Test that section is skipped when no sortings."""
        mock_rnc_client.get_corpus_config.return_value = CORPUS_CONFIG_NO_SORTINGS
        mock_rnc_client.get_attributes.return_value = ATTRIBUTES_EMPTY

        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        assert "No sorting methods available" in result or "_No sorting methods_" in result

    @pytest.mark.asyncio
    async def test_grammar_attributes_section(
            self, mock_rnc_client, mock_env_token):
        """Test grammar attributes section."""
        mock_rnc_client.get_corpus_config.return_value = CORPUS_CONFIG_MAIN
        mock_rnc_client.get_attributes.return_value = ATTRIBUTES_GRAMMAR

        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        assert "## Grammar Tags" in result

    @pytest.mark.asyncio
    async def test_missing_attribute_graceful_degradation(
            self, mock_rnc_client, mock_env_token):
        """Test graceful degradation when attribute fetch fails."""
        mock_rnc_client.get_corpus_config.return_value = CORPUS_CONFIG_MAIN
        # Simulate failure for one attribute type
        mock_rnc_client.get_attributes.side_effect = Exception("API Error")

        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        # Should still return markdown (not raise exception)
        assert isinstance(result, str)
        assert "_No gr tags available._" in result or "_No sem tags available._" in result

    @pytest.mark.asyncio
    async def test_always_returns_string(
            self, mock_rnc_client, mock_env_token):
        """Test that generator always returns string (never raises)."""
        mock_rnc_client.get_corpus_config.side_effect = Exception(
            "Config fetch failed")

        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        assert isinstance(result, str)
        assert "Error loading resource" in result


@pytest.mark.unit
class TestOptionFormatting:
    """Tests for option formatting."""

    def test_format_leaf_nodes(self):
        """Test formatting of leaf nodes (no suboptions)."""
        options = [
            {"value": "S", "title": "Существительное"}
        ]

        generator = CorpusResourceGenerator(None)
        result = generator._format_options(options)

        assert "`S`" in result
        assert "Существительное" in result

    def test_format_nested_hierarchy(self):
        """Test formatting of nested hierarchy."""
        options = [
            {
                "value": "S",
                "title": "Существительное",
                "suboptions": {
                    "options": [
                        {"value": "nom", "title": "Именительный падеж"}
                    ]
                }
            }
        ]

        generator = CorpusResourceGenerator(None)
        result = generator._format_options(options)

        assert "`S`" in result
        assert "Существительное" in result
        assert "`nom`" in result
        assert "  " in result  # Indentation

    def test_format_category_header_only(self):
        """Test formatting of category header (no value)."""
        options = [
            {
                "title": "Таксономия",
                "suboptions": {
                    "options": [
                        {"value": "t:hum", "title": "Человек"}
                    ]
                }
            }
        ]

        generator = CorpusResourceGenerator(None)
        result = generator._format_options(options)

        assert "**Таксономия**" in result
        assert "`t:hum`" in result

    def test_format_empty_options(self):
        """Test formatting of empty options list."""
        generator = CorpusResourceGenerator(None)
        result = generator._format_options([])

        assert result == ""


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_missing_token_returns_error_message(
            self, mock_rnc_client, clear_env_token):
        """Test that missing token returns error message string."""
        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        assert isinstance(result, str)
        assert "Error loading resource" in result

    @pytest.mark.asyncio
    async def test_api_error_on_config_fetch(
            self, mock_rnc_client, mock_env_token):
        """Test API error on config fetch returns error message."""
        mock_rnc_client.get_corpus_config.side_effect = Exception(
            "Network error")

        generator = CorpusResourceGenerator(mock_rnc_client)
        result = await generator.generate("MAIN")

        assert isinstance(result, str)
        assert "Error loading resource" in result

    @pytest.mark.asyncio
    async def test_never_raises_exception(
            self, mock_rnc_client, mock_env_token):
        """Test that generator never raises exceptions."""
        # Simulate all kinds of failures
        mock_rnc_client.get_corpus_config.side_effect = Exception("Error 1")
        mock_rnc_client.get_attributes.side_effect = Exception("Error 2")

        generator = CorpusResourceGenerator(mock_rnc_client)

        # Should not raise
        result = await generator.generate("MAIN")
        assert isinstance(result, str)
