"""Unit tests for string representations of schemas."""

import pytest
from rnc_mcp.schemas.schemas import (
    TokenRequest,
    DateFilter,
    SubcorpusFilter,
    SearchQuery,
    RncCorpusType
)


@pytest.mark.unit
class TestStringRepresentations:

    def test_date_filter_repr(self):
        """Test formatting of date ranges."""
        d1 = DateFilter(start_year=1800, end_year=1900)
        assert str(d1) == "1800-1900"

        d2 = DateFilter(start_year=1900)
        assert str(d2) == "1900-"

        d3 = DateFilter(end_year=2000)
        assert str(d3) == "-2000"

    def test_token_request_repr_compact(self):
        """Test token string representation only shows present fields."""
        t = TokenRequest(lemma="бежать", gramm="V")
        s = str(t)
        assert "lemma='бежать'" in s
        assert "gr='V'" in s
        assert "sem=" not in s  # Should not be present
        assert "dist=" not in s  # Default distance should not be shown

    def test_token_request_repr_full(self):
        """Test token string with distances."""
        t = TokenRequest(lemma="x", dist_min=1, dist_max=3)
        s = str(t)
        assert "dist=1..3" in s

    def test_search_query_multiline(self):
        """Test that search query produces a multiline report."""
        q = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="тест")],
            subcorpus=SubcorpusFilter(author="Пушкин")
        )
        s = str(q)
        assert "SearchQuery (MAIN):" in s
        assert "  Tokens:" in s
        assert "    1. Token[lemma='тест']" in s
        assert "  Subcorpus: author='Пушкин'" in s

    def test_empty_subcorpus_repr(self):
        """Test subcorpus string only shows set fields."""
        sc = SubcorpusFilter(author="Толстой")
        assert str(sc) == "author='Толстой'"
        assert "date=" not in str(sc)
