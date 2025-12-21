"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError
from rnc_mcp.schemas.schemas import (
    TokenRequest,
    DateFilter,
    SubcorpusFilter,
    SearchQuery,
    RncCorpusType,
    DocMetadata,
    DocumentItem,
    StatValues,
    GlobalStats,
    ConcordanceResponse,
)


@pytest.mark.unit
class TestTokenRequest:
    """Tests for TokenRequest schema validation."""

    def test_all_fields_optional(self):
        """Test that all linguistic fields are optional."""
        # Should be able to create with no parameters
        token = TokenRequest()
        assert token.lemma is None
        assert token.wordform is None
        assert token.gramm is None
        assert token.semantic is None
        assert token.syntax is None
        assert token.flags is None

    def test_default_dist_values(self):
        """Test default distance values."""
        token = TokenRequest()
        assert token.dist_min == 1
        assert token.dist_max == 1

    def test_accepts_all_linguistic_params(self):
        """Test that all linguistic parameters can be set."""
        token = TokenRequest(
            lemma="бежать",
            wordform="бежал",
            gramm="V",
            semantic="t:hum",
            syntax="root",
            flags="capital"
        )
        assert token.lemma == "бежать"
        assert token.wordform == "бежал"
        assert token.gramm == "V"
        assert token.semantic == "t:hum"
        assert token.syntax == "root"
        assert token.flags == "capital"

    def test_accepts_custom_distance_ranges(self):
        """Test custom distance min/max values."""
        token = TokenRequest(dist_min=0, dist_max=5)
        assert token.dist_min == 0
        assert token.dist_max == 5

    def test_accepts_negative_distance_values(self):
        """Test that negative distance values are allowed."""
        token = TokenRequest(dist_min=-2, dist_max=2)
        assert token.dist_min == -2
        assert token.dist_max == 2

    def test_accepts_empty_strings(self):
        """Test that empty strings are allowed for linguistic fields."""
        token = TokenRequest(
            lemma="",
            wordform="",
            gramm=""
        )
        assert token.lemma == ""
        assert token.wordform == ""
        assert token.gramm == ""


@pytest.mark.unit
class TestDateFilter:
    """Tests for DateFilter schema validation."""

    def test_both_years_optional(self):
        """Test that both year fields are optional."""
        date_filter = DateFilter()
        assert date_filter.start_year is None
        assert date_filter.end_year is None

    def test_start_year_only(self):
        """Test DateFilter with only start_year."""
        date_filter = DateFilter(start_year=1900)
        assert date_filter.start_year == 1900
        assert date_filter.end_year is None

    def test_end_year_only(self):
        """Test DateFilter with only end_year."""
        date_filter = DateFilter(end_year=2000)
        assert date_filter.start_year is None
        assert date_filter.end_year == 2000

    def test_both_years(self):
        """Test DateFilter with both years."""
        date_filter = DateFilter(start_year=1800, end_year=1900)
        assert date_filter.start_year == 1800
        assert date_filter.end_year == 1900

    def test_start_greater_than_end_not_validated(self):
        """Test that start > end is not validated (known gap)."""
        # This should succeed even though logically incorrect
        date_filter = DateFilter(start_year=2000, end_year=1900)
        assert date_filter.start_year == 2000
        assert date_filter.end_year == 1900

    def test_accepts_negative_years(self):
        """Test that negative years are accepted (no validation)."""
        date_filter = DateFilter(start_year=-100, end_year=100)
        assert date_filter.start_year == -100
        assert date_filter.end_year == 100

    def test_accepts_future_years(self):
        """Test that future years are accepted (no validation)."""
        date_filter = DateFilter(start_year=2100, end_year=2200)
        assert date_filter.start_year == 2100
        assert date_filter.end_year == 2200


@pytest.mark.unit
class TestSubcorpusFilter:
    """Tests for SubcorpusFilter schema validation."""

    def test_all_fields_optional(self):
        """Test that all subcorpus filter fields are optional."""
        subcorpus = SubcorpusFilter()
        assert subcorpus.author is None
        assert subcorpus.title is None
        assert subcorpus.date_range is None
        assert subcorpus.author_gender is None
        assert subcorpus.author_birthyear_range is None
        assert subcorpus.disambiguation is None

    def test_author_gender_literal_values(self):
        """Test author_gender accepts only 'male' and 'female'."""
        # Valid values
        subcorpus_male = SubcorpusFilter(author_gender="male")
        assert subcorpus_male.author_gender == "male"

        subcorpus_female = SubcorpusFilter(author_gender="female")
        assert subcorpus_female.author_gender == "female"

    def test_invalid_gender_raises_validation_error(self):
        """Test that invalid gender value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SubcorpusFilter(author_gender="other")

        assert "author_gender" in str(exc_info.value)

    def test_disambiguation_literal_values(self):
        """Test disambiguation accepts only 'auto' and 'manual'."""
        # Valid values
        subcorpus_auto = SubcorpusFilter(disambiguation="auto")
        assert subcorpus_auto.disambiguation == "auto"

        subcorpus_manual = SubcorpusFilter(disambiguation="manual")
        assert subcorpus_manual.disambiguation == "manual"

    def test_invalid_disambiguation_raises_validation_error(self):
        """Test that invalid disambiguation value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SubcorpusFilter(disambiguation="invalid")

        assert "disambiguation" in str(exc_info.value)

    def test_accepts_nested_date_filter_objects(self):
        """Test that DateFilter objects can be nested."""
        subcorpus = SubcorpusFilter(
            date_range=DateFilter(start_year=1900, end_year=2000),
            author_birthyear_range=DateFilter(start_year=1850, end_year=1900)
        )
        assert subcorpus.date_range.start_year == 1900
        assert subcorpus.date_range.end_year == 2000
        assert subcorpus.author_birthyear_range.start_year == 1850
        assert subcorpus.author_birthyear_range.end_year == 1900

    def test_all_fields_together(self):
        """Test SubcorpusFilter with all fields set."""
        subcorpus = SubcorpusFilter(
            author="Пушкин",
            title="Евгений Онегин",
            date_range=DateFilter(start_year=1830, end_year=1840),
            author_gender="male",
            author_birthyear_range=DateFilter(start_year=1799, end_year=1799),
            disambiguation="auto"
        )
        assert subcorpus.author == "Пушкин"
        assert subcorpus.title == "Евгений Онегин"
        assert subcorpus.author_gender == "male"
        assert subcorpus.disambiguation == "auto"


@pytest.mark.unit
class TestSearchQuery:
    """Tests for SearchQuery schema validation."""

    def test_default_corpus_is_main(self):
        """Test that default corpus is MAIN."""
        query = SearchQuery(tokens=[TokenRequest(lemma="тест")])
        assert query.corpus == RncCorpusType.MAIN

    def test_valid_corpus_types(self):
        """Test that all valid corpus types are accepted."""
        for corpus_type in RncCorpusType:
            query = SearchQuery(
                corpus=corpus_type,
                tokens=[TokenRequest(lemma="тест")]
            )
            assert query.corpus == corpus_type

    def test_invalid_corpus_raises_validation_error(self):
        """Test that invalid corpus type raises ValidationError."""
        with pytest.raises(ValidationError):
            SearchQuery(
                corpus="INVALID",
                tokens=[TokenRequest(lemma="тест")]
            )

    def test_tokens_min_length_one(self):
        """Test that tokens list requires at least one token."""
        # Valid: one token
        query = SearchQuery(tokens=[TokenRequest(lemma="тест")])
        assert len(query.tokens) == 1

        # Valid: multiple tokens
        query = SearchQuery(tokens=[
            TokenRequest(lemma="тест1"),
            TokenRequest(lemma="тест2")
        ])
        assert len(query.tokens) == 2

    def test_empty_tokens_raises_validation_error(self):
        """Test that empty tokens list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(tokens=[])

        assert "tokens" in str(exc_info.value)

    def test_default_pagination(self):
        """Test default pagination values."""
        query = SearchQuery(tokens=[TokenRequest(lemma="тест")])
        assert query.page == 0
        assert query.per_page == 10

    def test_default_return_examples_true(self):
        """Test that return_examples defaults to True."""
        query = SearchQuery(tokens=[TokenRequest(lemma="тест")])
        assert query.return_examples is True

    def test_invalid_sort_not_validated_client_side(self):
        """Test that invalid sort values are not validated (known gap)."""
        # This should succeed even with invalid sort
        query = SearchQuery(
            tokens=[TokenRequest(lemma="тест")],
            sort="invalid_sort_method"
        )
        assert query.sort == "invalid_sort_method"

    def test_negative_page_not_validated(self):
        """Test that negative page is not validated (known gap)."""
        query = SearchQuery(
            tokens=[TokenRequest(lemma="тест")],
            page=-1
        )
        assert query.page == -1

    def test_negative_per_page_not_validated(self):
        """Test that negative per_page is not validated (known gap)."""
        query = SearchQuery(
            tokens=[TokenRequest(lemma="тест")],
            per_page=-10
        )
        assert query.per_page == -10

    def test_with_all_optional_fields(self):
        """Test SearchQuery with all optional fields set."""
        query = SearchQuery(
            corpus=RncCorpusType.PAPER,
            tokens=[
                TokenRequest(lemma="идти", gramm="V"),
                TokenRequest(wordform="дождь", dist_min=1, dist_max=3)
            ],
            subcorpus=SubcorpusFilter(
                author="Пушкин",
                title="Евгений Онегин",
                date_range=DateFilter(start_year=1830, end_year=1840),
                author_gender="male"
            ),
            sort="grcreated",
            page=2,
            per_page=50,
            return_examples=False
        )
        assert query.corpus == RncCorpusType.PAPER
        assert len(query.tokens) == 2
        assert query.subcorpus.author == "Пушкин"
        assert query.sort == "grcreated"
        assert query.page == 2
        assert query.per_page == 50
        assert query.return_examples is False


@pytest.mark.unit
class TestResponseSchemas:
    """Tests for response schemas."""

    def test_doc_metadata_title_required(self):
        """Test that DocMetadata requires title."""
        metadata = DocMetadata(title="Test Title")
        assert metadata.title == "Test Title"
        assert metadata.author is None
        assert metadata.year is None

    def test_doc_metadata_author_optional(self):
        """Test that author is optional."""
        metadata = DocMetadata(title="Test", author="Author")
        assert metadata.author == "Author"

    def test_doc_metadata_year_optional(self):
        """Test that year is optional."""
        metadata = DocMetadata(title="Test", year="2000")
        assert metadata.year == "2000"

    def test_doc_metadata_all_fields(self):
        """Test DocMetadata with all fields."""
        metadata = DocMetadata(
            title="Евгений Онегин",
            author="Пушкин А.С.",
            year="1837"
        )
        assert metadata.title == "Евгений Онегин"
        assert metadata.author == "Пушкин А.С."
        assert metadata.year == "1837"

    def test_document_item_requires_metadata_and_examples(self):
        """Test that DocumentItem requires both metadata and examples."""
        metadata = DocMetadata(title="Test")
        doc = DocumentItem(
            metadata=metadata,
            examples=["example1", "example2"]
        )
        assert doc.metadata.title == "Test"
        assert len(doc.examples) == 2

    def test_document_item_examples_can_be_empty_list(self):
        """Test that examples can be an empty list."""
        metadata = DocMetadata(title="Test")
        doc = DocumentItem(metadata=metadata, examples=[])
        assert doc.examples == []

    def test_stat_values_all_optional(self):
        """Test that all StatValues fields are optional (can be None)."""
        stats = StatValues()
        assert stats.textCount is None
        assert stats.wordUsageCount is None

    def test_stat_values_with_values(self):
        """Test StatValues with actual values."""
        stats = StatValues(textCount=1000, wordUsageCount=50000)
        assert stats.textCount == 1000
        assert stats.wordUsageCount == 50000

    def test_global_stats_structure(self):
        """Test GlobalStats structure validation."""
        stats = GlobalStats(
            corpusStats=StatValues(textCount=1000000),
            subcorpStats=StatValues(textCount=50000),
            queryStats=StatValues(textCount=150),
            total_pages_available=10
        )
        assert stats.corpusStats.textCount == 1000000
        assert stats.subcorpStats.textCount == 50000
        assert stats.queryStats.textCount == 150
        assert stats.total_pages_available == 10

    def test_global_stats_total_pages_required(self):
        """Test that total_pages_available is required."""
        stats = GlobalStats(total_pages_available=0)
        assert stats.total_pages_available == 0

    def test_global_stats_stat_fields_optional(self):
        """Test that stat fields can be None."""
        stats = GlobalStats(
            corpusStats=None,
            subcorpStats=None,
            queryStats=None,
            total_pages_available=0
        )
        assert stats.corpusStats is None
        assert stats.subcorpStats is None
        assert stats.queryStats is None

    def test_concordance_response_structure(self):
        """Test ConcordanceResponse structure."""
        response = ConcordanceResponse(
            stats=GlobalStats(total_pages_available=5),
            results=[
                DocumentItem(
                    metadata=DocMetadata(title="Doc1"),
                    examples=["example"]
                )
            ]
        )
        assert response.stats.total_pages_available == 5
        assert len(response.results) == 1
        assert response.results[0].metadata.title == "Doc1"

    def test_concordance_response_empty_results(self):
        """Test ConcordanceResponse with empty results."""
        response = ConcordanceResponse(
            stats=GlobalStats(total_pages_available=0),
            results=[]
        )
        assert response.stats.total_pages_available == 0
        assert response.results == []
