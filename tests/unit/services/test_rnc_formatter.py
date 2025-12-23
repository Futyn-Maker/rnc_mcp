"""Unit tests for ResponseFormatter."""

import pytest
from rnc_mcp.services.rnc_formatter import RNCResponseFormatter
from rnc_mcp.schemas.schemas import ConcordanceResponse, DocMetadata
from tests.fixtures.mock_responses import (
    CONCORDANCE_SUCCESS,
    CONCORDANCE_EMPTY,
    CONCORDANCE_MISSING_METADATA,
    CONCORDANCE_NO_HITS,
    CONCORDANCE_MULTIPLE_DOCS,
)


@pytest.mark.unit
class TestMetadataExtraction:
    """Tests for _extract_meta method."""

    def test_full_explain_info(self):
        """Test metadata extraction with full docExplainInfo."""
        doc_info = {"title": "Test Title",
                    "docExplainInfo": {"items": [{"parsingFields": [{"name": "author",
                                                                     "value": [{"valString": {"v": "Пушкин"}}]},
                                                                    {"name": "created",
                                                                     "value": [{"valString": {"v": "1837"}}]},
                                                                    {"name": "header",
                                                                     "value": [{"valString": {"v": "Евгений Онегин"}}]}]}]}}

        metadata = RNCResponseFormatter._extract_meta(doc_info)

        assert metadata.title == "Test Title"  # Title takes precedence
        assert metadata.author == "Пушкин"
        assert metadata.year == "1837"

    def test_missing_explain_info(self):
        """Test metadata extraction when docExplainInfo is missing."""
        doc_info = {"title": "Test Title"}

        metadata = RNCResponseFormatter._extract_meta(doc_info)

        assert metadata.title == "Test Title"
        assert metadata.author is None
        assert metadata.year is None

    def test_empty_parsing_fields(self):
        """Test metadata extraction with empty parsingFields."""
        doc_info = {
            "title": "Default Title",
            "docExplainInfo": {
                "items": [
                    {"parsingFields": []}
                ]
            }
        }

        metadata = RNCResponseFormatter._extract_meta(doc_info)

        assert metadata.title == "Default Title"
        assert metadata.author is None
        assert metadata.year is None

    def test_author_field_only(self):
        """Test metadata extraction with author field only."""
        doc_info = {
            "title": "Test",
            "docExplainInfo": {
                "items": [
                    {
                        "parsingFields": [
                            {
                                "name": "author",
                                "value": [{"valString": {"v": "Толстой"}}]
                            }
                        ]
                    }
                ]
            }
        }

        metadata = RNCResponseFormatter._extract_meta(doc_info)

        assert metadata.author == "Толстой"
        assert metadata.year is None

    def test_year_field_only(self):
        """Test metadata extraction with year field only."""
        doc_info = {
            "title": "Test",
            "docExplainInfo": {
                "items": [
                    {
                        "parsingFields": [
                            {
                                "name": "created",
                                "value": [{"valString": {"v": "1900"}}]
                            }
                        ]
                    }
                ]
            }
        }

        metadata = RNCResponseFormatter._extract_meta(doc_info)

        assert metadata.year == "1900"
        assert metadata.author is None

    def test_header_fallback_for_title(self):
        """Test that header field is used as fallback title."""
        doc_info = {
            "title": "Unknown Title",
            "docExplainInfo": {
                "items": [
                    {
                        "parsingFields": [
                            {
                                "name": "header",
                                "value": [{"valString": {"v": "Анна Каренина"}}]
                            }
                        ]
                    }
                ]
            }
        }

        metadata = RNCResponseFormatter._extract_meta(doc_info)

        assert metadata.title == "Анна Каренина"

    def test_unknown_title_default(self):
        """Test Unknown Title default when no title or header."""
        doc_info = {}

        metadata = RNCResponseFormatter._extract_meta(doc_info)
        assert metadata.title == "Unknown Title"

    def test_empty_value_array(self):
        """Test handling of empty value arrays."""
        doc_info = {
            "title": "Test",
            "docExplainInfo": {
                "items": [
                    {
                        "parsingFields": [
                            {
                                "name": "author",
                                "value": []
                            }
                        ]
                    }
                ]
            }
        }

        metadata = RNCResponseFormatter._extract_meta(doc_info)

        assert metadata.author is None


@pytest.mark.unit
class TestSnippetHighlighting:
    """Tests for _format_snippet_text method."""

    def test_single_hit_word(self):
        """Test highlighting single hit word."""
        words = [
            {"text": "Я", "displayParams": {}},
            {"text": " ", "displayParams": {}},
            {"text": "помню", "displayParams": {"hit": True}},
            {"text": " ", "displayParams": {}},
            {"text": "чудное", "displayParams": {}}
        ]

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text == "Я **помню** чудное"

    def test_multiple_consecutive_hits(self):
        """Test highlighting multiple consecutive hits."""
        words = [
            {"text": "word1", "displayParams": {}},
            {"text": " ", "displayParams": {}},
            {"text": "hit1", "displayParams": {"hit": True}},
            {"text": " ", "displayParams": {}},
            {"text": "hit2", "displayParams": {"hit": True}},
            {"text": " ", "displayParams": {}},
            {"text": "word2", "displayParams": {}}
        ]

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text == "word1 **hit1 hit2** word2"

    def test_no_hits(self):
        """Test snippet with no hits (empty hit_indices)."""
        words = [
            {"text": "word1", "displayParams": {}},
            {"text": " ", "displayParams": {}},
            {"text": "word2", "displayParams": {}}
        ]

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text == "word1 word2"

    def test_empty_words_array(self):
        """Test empty words array returns empty string."""
        words = []

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text == ""

    def test_first_word_is_hit(self):
        """Test highlighting when first word is a hit."""
        words = [
            {"text": "first", "displayParams": {"hit": True}},
            {"text": " ", "displayParams": {}},
            {"text": "second", "displayParams": {}}
        ]

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text.startswith("**first")

    def test_last_word_is_hit(self):
        """Test highlighting when last word is a hit."""
        words = [
            {"text": "first", "displayParams": {}},
            {"text": " ", "displayParams": {}},
            {"text": "last", "displayParams": {"hit": True}}
        ]

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text.endswith("last**")

    def test_all_words_concatenated(self):
        """Test that all words are concatenated (no spaces added)."""
        words = [
            {"text": "a", "displayParams": {}},
            {"text": "b", "displayParams": {}},
            {"text": "c", "displayParams": {}}
        ]

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text == "abc"

    def test_missing_text_field(self):
        """Test handling of missing text field."""
        words = [
            {"displayParams": {}},
            {"text": "word", "displayParams": {}}
        ]

        text = RNCResponseFormatter._format_snippet_text(words)

        assert text == "word"


@pytest.mark.unit
class TestStatsParsing:
    """Tests for stats parsing."""

    def test_all_stats_present(self):
        """Test parsing when all stats are present."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_SUCCESS)

        assert response.stats.corpusStats is not None
        assert response.stats.corpusStats.textCount == 1000000
        assert response.stats.corpusStats.wordUsageCount == 500000000

        assert response.stats.subcorpStats is not None
        assert response.stats.subcorpStats.textCount == 50000

        assert response.stats.queryStats is not None
        assert response.stats.queryStats.textCount == 150

    def test_missing_stats_return_none(self):
        """Test that missing stats return None."""
        raw_response = {
            "pagination": {"totalPageCount": 0},
            "groups": []
        }

        response = RNCResponseFormatter.format_search_results(raw_response)

        assert response.stats.corpusStats is None
        assert response.stats.subcorpStats is None
        assert response.stats.queryStats is None

    def test_null_values_in_stats_preserved(self):
        """Test that null values in stats are preserved."""
        raw_response = {
            "corpusStats": {"textCount": 100, "wordUsageCount": None},
            "pagination": {"totalPageCount": 1},
            "groups": []
        }

        response = RNCResponseFormatter.format_search_results(raw_response)

        assert response.stats.corpusStats.textCount == 100
        assert response.stats.corpusStats.wordUsageCount is None

    def test_total_pages_from_pagination(self):
        """Test extraction of total_pages_available from pagination."""
        raw_response = {
            "pagination": {"totalPageCount": 42},
            "groups": []
        }

        response = RNCResponseFormatter.format_search_results(raw_response)

        assert response.stats.total_pages_available == 42

    def test_missing_pagination_defaults_to_zero(self):
        """Test that missing pagination defaults to 0."""
        raw_response = {"groups": []}

        response = RNCResponseFormatter.format_search_results(raw_response)

        assert response.stats.total_pages_available == 0


@pytest.mark.unit
class TestFullResponseFormatting:
    """Tests for format_search_results method."""

    def test_response_with_results(self):
        """Test formatting response with results."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_SUCCESS)

        assert isinstance(response, ConcordanceResponse)
        assert len(response.results) > 0
        assert response.stats is not None

    def test_empty_groups_array(self):
        """Test response with empty groups array."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_EMPTY)

        assert len(response.results) == 0
        assert response.stats.queryStats.textCount == 0

    def test_multiple_documents(self):
        """Test formatting response with multiple documents."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_MULTIPLE_DOCS)

        assert len(response.results) == 2
        assert response.results[0].metadata.author == "Author 1"
        assert response.results[1].metadata.author == "Author 2"

    def test_multiple_snippets_per_document(self):
        """Test document with multiple snippets."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_MULTIPLE_DOCS)

        # Second document has 2 snippets
        assert len(response.results[1].examples) == 2

    def test_nested_structure_traversal(self):
        """Test traversal of groups → docs → snippetGroups → snippets → sequences → words."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_SUCCESS)

        # Should successfully extract examples from deeply nested structure
        assert len(response.results) > 0
        assert len(response.results[0].examples) > 0

    def test_filters_out_empty_examples(self):
        """Test that documents without examples are filtered out."""
        raw_response = {"pagination": {"totalPageCount": 1},
                        "groups": [{"docs": [{"info": {"title": "Doc with snippets"},
                                              "snippetGroups": [{"snippets": [{"sequences": [{"words": [{"text": "word",
                                                                                                         "displayParams": {"hit": True}}]}]}]}]},
                                             {"info": {"title": "Doc without snippets"},
                                              "snippetGroups": []}]}]}

        response = RNCResponseFormatter.format_search_results(raw_response)

        # Only document with examples should be included
        assert len(response.results) == 1
        assert response.results[0].metadata.title == "Doc with snippets"

    def test_missing_fields_handled_with_get_defaults(self):
        """Test that missing fields are handled gracefully."""
        raw_response = {
            "pagination": {},
            "groups": [
                {
                    "docs": [
                        {
                            "info": {},
                            "snippetGroups": [
                                {
                                    "snippets": [
                                        {
                                            "sequences": [
                                                {
                                                    "words": [{"text": "test"}]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        response = RNCResponseFormatter.format_search_results(raw_response)

        # Should not raise exceptions
        assert response.stats.total_pages_available == 0
        assert len(response.results) == 1

    def test_concordance_response_structure(self):
        """Test that response matches ConcordanceResponse structure."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_SUCCESS)

        assert hasattr(response, 'stats')
        assert hasattr(response, 'results')
        assert hasattr(response.stats, 'corpusStats')
        assert hasattr(response.stats, 'subcorpStats')
        assert hasattr(response.stats, 'queryStats')
        assert hasattr(response.stats, 'total_pages_available')

    def test_missing_metadata_response(self):
        """Test formatting response with missing metadata."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_MISSING_METADATA)

        assert len(response.results) == 1
        assert response.results[0].metadata.title == "Document without metadata"
        assert response.results[0].metadata.author is None

    def test_no_hits_response(self):
        """Test formatting response with no hit highlighting."""
        response = RNCResponseFormatter.format_search_results(
            CONCORDANCE_NO_HITS)

        assert len(response.results) == 1
        # Text should still be formatted even without hits
        assert len(response.results[0].examples) == 1
        assert "**" not in response.results[0].examples[0]
