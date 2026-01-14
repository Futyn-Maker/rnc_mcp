"""Unit tests for RNCQueryBuilder."""

import pytest
from rnc_mcp.services.rnc_builder import RNCQueryBuilder
from rnc_mcp.schemas.schemas import (
    SearchQuery,
    TokenRequest,
    SubcorpusFilter,
    DateFilter,
    RncCorpusType,
)


@pytest.mark.unit
class TestTokenConditionBuilding:
    """Tests for _build_token_conditions method."""

    def test_lemma_only(self):
        """Test token condition with lemma only."""
        token = TokenRequest(lemma="бежать")
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 1
        assert conditions[0] == {"fieldName": "lex", "text": {"v": "бежать"}}

    def test_wordform_only(self):
        """Test token condition with wordform only."""
        token = TokenRequest(wordform="бежал")
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 1
        assert conditions[0] == {"fieldName": "form", "text": {"v": "бежал"}}

    def test_gramm_only(self):
        """Test token condition with grammar tag only."""
        token = TokenRequest(gramm="V")
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 1
        assert conditions[0] == {"fieldName": "gramm", "text": {"v": "V"}}

    def test_semantic_only(self):
        """Test token condition with semantic tag only."""
        token = TokenRequest(semantic="t:hum")
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 1
        assert conditions[0] == {"fieldName": "sem", "text": {"v": "t:hum"}}

    def test_syntax_only(self):
        """Test token condition with syntax tag only."""
        token = TokenRequest(syntax="root")
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 1
        assert conditions[0] == {"fieldName": "syntax", "text": {"v": "root"}}

    def test_flags_only(self):
        """Test token condition with flags only."""
        token = TokenRequest(flags="capital")
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 1
        assert conditions[0] == {
            "fieldName": "flags", "text": {
                "v": "capital"}}

    def test_multiple_fields_combined(self):
        """Test token with multiple fields."""
        token = TokenRequest(lemma="идти", gramm="V")
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 2
        assert {"fieldName": "lex", "text": {"v": "идти"}} in conditions
        assert {"fieldName": "gramm", "text": {"v": "V"}} in conditions

    def test_all_fields_together(self):
        """Test token with all linguistic fields."""
        token = TokenRequest(
            lemma="идти",
            wordform="идёт",
            gramm="V",
            syntax="root",
            flags="capital"
        )
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert len(conditions) == 5
        assert {"fieldName": "lex", "text": {"v": "идти"}} in conditions
        assert {"fieldName": "form", "text": {"v": "идёт"}} in conditions
        assert {"fieldName": "gramm", "text": {"v": "V"}} in conditions
        assert {"fieldName": "syntax", "text": {"v": "root"}} in conditions
        assert {"fieldName": "flags", "text": {"v": "capital"}} in conditions

    def test_empty_token_returns_empty_list(self):
        """Test that empty token (no attributes) returns empty conditions list."""
        token = TokenRequest()
        conditions = RNCQueryBuilder._build_token_conditions(token)

        assert conditions == []


@pytest.mark.unit
class TestDistanceCondition:
    """Tests for _build_dist_condition method."""

    def test_default_distance(self):
        """Test distance condition with default values (1-1)."""
        dist_cond = RNCQueryBuilder._build_dist_condition(1, 1)

        assert dist_cond == {
            "fieldName": "dist",
            "intRange": {"begin": 1, "end": 1}
        }

    def test_custom_range(self):
        """Test distance condition with custom range."""
        dist_cond = RNCQueryBuilder._build_dist_condition(0, 5)

        assert dist_cond == {
            "fieldName": "dist",
            "intRange": {"begin": 0, "end": 5}
        }

    def test_negative_distances(self):
        """Test distance condition with negative values."""
        dist_cond = RNCQueryBuilder._build_dist_condition(-2, 2)

        assert dist_cond == {
            "fieldName": "dist",
            "intRange": {"begin": -2, "end": 2}
        }


@pytest.mark.unit
class TestDateRangeBuilding:
    """Tests for _build_date_range_condition method."""

    def test_start_year_only(self):
        """Test date range with start year only."""
        date_filter = DateFilter(start_year=1900)
        date_cond = RNCQueryBuilder._build_date_range_condition(date_filter)

        assert date_cond is not None
        assert date_cond["fieldName"] == "created"
        assert date_cond["dateRange"]["matching"] == "INT_RANGE_INTERSECT"
        assert date_cond["dateRange"]["begin"] == {
            "year": 1900, "month": 1, "day": 1}
        assert "end" not in date_cond["dateRange"]

    def test_end_year_only(self):
        """Test date range with end year only."""
        date_filter = DateFilter(end_year=2000)
        date_cond = RNCQueryBuilder._build_date_range_condition(date_filter)

        assert date_cond is not None
        assert date_cond["fieldName"] == "created"
        assert date_cond["dateRange"]["end"] == {
            "year": 2000, "month": 12, "day": 31}
        assert "begin" not in date_cond["dateRange"]

    def test_both_years(self):
        """Test date range with both start and end years."""
        date_filter = DateFilter(start_year=1800, end_year=1900)
        date_cond = RNCQueryBuilder._build_date_range_condition(date_filter)

        assert date_cond is not None
        assert date_cond["dateRange"]["begin"] == {
            "year": 1800, "month": 1, "day": 1}
        assert date_cond["dateRange"]["end"] == {
            "year": 1900, "month": 12, "day": 31}

    def test_empty_date_filter_returns_none(self):
        """Test that empty DateFilter returns None."""
        date_filter = DateFilter()
        date_cond = RNCQueryBuilder._build_date_range_condition(date_filter)

        assert date_cond is None

    def test_date_format_full_date(self):
        """Test that dates are formatted as full date objects."""
        date_filter = DateFilter(start_year=1950, end_year=1960)
        date_cond = RNCQueryBuilder._build_date_range_condition(date_filter)

        # Start is January 1st
        assert date_cond["dateRange"]["begin"]["month"] == 1
        assert date_cond["dateRange"]["begin"]["day"] == 1

        # End is December 31st
        assert date_cond["dateRange"]["end"]["month"] == 12
        assert date_cond["dateRange"]["end"]["day"] == 31


@pytest.mark.unit
class TestSubcorpusConditionBuilding:
    """Tests for _build_subcorpus_conditions method."""

    def test_disambiguation_condition(self):
        """Test subcorpus with disambiguation."""
        subcorpus = SubcorpusFilter(disambiguation="auto")
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        assert {"fieldName": "tagging", "text": {"v": "auto"}} in conditions

    def test_title_condition(self):
        """Test subcorpus with title filter."""
        subcorpus = SubcorpusFilter(title="Евгений Онегин")
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        assert {"fieldName": "header", "text": {
            "v": "Евгений Онегин"}} in conditions

    def test_date_range_condition(self):
        """Test subcorpus with date range (uses dateRange)."""
        subcorpus = SubcorpusFilter(
            date_range=DateFilter(start_year=1830, end_year=1840)
        )
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        # Find the created date condition
        date_cond = next(c for c in conditions if c["fieldName"] == "created")
        assert date_cond["dateRange"]["begin"] == {
            "year": 1830, "month": 1, "day": 1}
        assert date_cond["dateRange"]["end"] == {
            "year": 1840, "month": 12, "day": 31}

    def test_author_condition(self):
        """Test subcorpus with author filter."""
        subcorpus = SubcorpusFilter(author="Пушкин")
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        assert {"fieldName": "author", "text": {"v": "Пушкин"}} in conditions

    def test_gender_male_translation(self):
        """Test that 'male' is translated to 'муж'."""
        subcorpus = SubcorpusFilter(author_gender="male")
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        assert {"fieldName": "sex", "text": {"v": "муж"}} in conditions

    def test_gender_female_translation(self):
        """Test that 'female' is translated to 'жен'."""
        subcorpus = SubcorpusFilter(author_gender="female")
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        assert {"fieldName": "sex", "text": {"v": "жен"}} in conditions

    def test_birthyear_range_uses_int_range(self):
        """Test that author birthyear uses intRange (not dateRange)."""
        subcorpus = SubcorpusFilter(
            author_birthyear_range=DateFilter(start_year=1799, end_year=1799)
        )
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        # Find the birthday condition
        birthday_cond = next(
            c for c in conditions if c["fieldName"] == "birthday")
        assert "intRange" in birthday_cond
        assert birthday_cond["intRange"]["begin"] == 1799
        assert birthday_cond["intRange"]["end"] == 1799

    def test_all_conditions_combined(self):
        """Test subcorpus with all filters."""
        subcorpus = SubcorpusFilter(
            disambiguation="manual",
            title="Война и мир",
            date_range=DateFilter(start_year=1860, end_year=1870),
            author="Толстой",
            author_gender="male",
            author_birthyear_range=DateFilter(start_year=1828, end_year=1828)
        )
        conditions = RNCQueryBuilder._build_subcorpus_conditions(subcorpus)

        assert len(conditions) == 6
        assert {"fieldName": "tagging", "text": {"v": "manual"}} in conditions
        assert {"fieldName": "header", "text": {
            "v": "Война и мир"}} in conditions
        assert {"fieldName": "author", "text": {"v": "Толстой"}} in conditions
        assert {"fieldName": "sex", "text": {"v": "муж"}} in conditions


@pytest.mark.unit
class TestFullPayloadBuilding:
    """Tests for build_payload method."""

    def test_minimal_query(self):
        """Test payload for minimal query (corpus + single token)."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="дом")]
        )
        payload = RNCQueryBuilder.build_payload(query)

        assert payload["corpus"]["type"] == "MAIN"
        assert "lexGramm" in payload
        assert len(payload["lexGramm"]) == 1
        assert "params" in payload

    def test_single_token_no_distance(self):
        """Test that first token has no distance condition."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="дом")]
        )
        payload = RNCQueryBuilder.build_payload(query)

        # Access token via sectionValues[0].subsectionValues[0]
        subsections = payload["lexGramm"]["sectionValues"][0]["subsectionValues"]
        assert len(subsections) == 1
        token_cond = subsections[0]["conditionValues"]

        # First token should not have distance
        field_names = [c["fieldName"] for c in token_cond]
        assert "dist" not in field_names

    def test_multiple_tokens_with_distances(self):
        """Test that subsequent tokens include distance conditions."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[
                TokenRequest(lemma="красный"),
                TokenRequest(lemma="цвет", dist_min=1, dist_max=1)
            ]
        )
        payload = RNCQueryBuilder.build_payload(query)

        # Access subsections
        subsections = payload["lexGramm"]["sectionValues"][0]["subsectionValues"]
        assert len(subsections) == 2

        # Second token should have distance
        second_token = subsections[1]["conditionValues"]
        field_names = [c["fieldName"] for c in second_token]
        assert "dist" in field_names

        # Find distance condition
        dist_cond = next(c for c in second_token if c["fieldName"] == "dist")
        assert dist_cond["intRange"]["begin"] == 1
        assert dist_cond["intRange"]["end"] == 1

    def test_with_subcorpus_filters(self):
        """Test payload with subcorpus filters."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="любовь")],
            subcorpus=SubcorpusFilter(author="Пушкин")
        )
        payload = RNCQueryBuilder.build_payload(query)

        # Subcorpus is at top level, not in params
        assert "subcorpus" in payload
        subcorpus_conds = payload["subcorpus"]["sectionValues"][0]["conditionValues"]
        assert {"fieldName": "author", "text": {
            "v": "Пушкин"}} in subcorpus_conds

    def test_with_sort_parameter(self):
        """Test payload with sort parameter."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="тест")],
            sort="grcreated"
        )
        payload = RNCQueryBuilder.build_payload(query)

        assert payload["params"]["sort"] == "grcreated"

    def test_pagination_defaults(self):
        """Test default pagination (page=0, per_page=10, snippets=50)."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="тест")]
        )
        payload = RNCQueryBuilder.build_payload(query)

        page_params = payload["params"]["pageParams"]
        assert page_params["page"] == 0
        assert page_params["docsPerPage"] == 10
        assert page_params["snippetsPerDoc"] == 50

    def test_return_examples_false_minimal_pagination(self):
        """Test that return_examples=False uses minimal pagination."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="тест")],
            return_examples=False
        )
        payload = RNCQueryBuilder.build_payload(query)

        page_params = payload["params"]["pageParams"]
        assert page_params["docsPerPage"] == 1
        assert page_params["snippetsPerDoc"] == 1

    def test_return_examples_true_custom_pagination(self):
        """Test that return_examples=True respects custom pagination."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="тест")],
            page=2,
            per_page=50,
            return_examples=True
        )
        payload = RNCQueryBuilder.build_payload(query)

        page_params = payload["params"]["pageParams"]
        assert page_params["page"] == 2
        assert page_params["docsPerPage"] == 50
        assert page_params["snippetsPerDoc"] == 50

    def test_payload_structure_matches_api(self):
        """Test that payload structure matches RNC API format."""
        query = SearchQuery(
            corpus=RncCorpusType.MAIN,
            tokens=[TokenRequest(lemma="тест")]
        )
        payload = RNCQueryBuilder.build_payload(query)

        # Top-level keys
        assert "corpus" in payload
        assert "lexGramm" in payload
        assert "params" in payload

        # Corpus structure
        assert "type" in payload["corpus"]

        # Params structure
        assert "pageParams" in payload["params"]

        # LexGramm structure
        assert "sectionValues" in payload["lexGramm"]
        section = payload["lexGramm"]["sectionValues"][0]
        assert "conditionValues" in section
        assert "subsectionValues" in section

    def test_complex_query_integration(self):
        """Test building payload for complex query."""
        query = SearchQuery(
            corpus=RncCorpusType.PAPER,
            tokens=[
                TokenRequest(lemma="идти", gramm="V"),
                TokenRequest(semantic="t:hum", dist_min=0, dist_max=3),
                TokenRequest(wordform="быстро", dist_min=1, dist_max=1)
            ],
            subcorpus=SubcorpusFilter(
                date_range=DateFilter(start_year=2000, end_year=2020),
                author_gender="female"
            ),
            sort="random",
            page=1,
            per_page=25,
            return_examples=True
        )
        payload = RNCQueryBuilder.build_payload(query)

        assert payload["corpus"]["type"] == "PAPER"

        # Check subsections for 3 tokens
        subsections = payload["lexGramm"]["sectionValues"][0]["subsectionValues"]
        assert len(subsections) == 3

        assert payload["params"]["sort"] == "random"
        assert payload["params"]["pageParams"]["page"] == 1
        assert payload["params"]["pageParams"]["docsPerPage"] == 25

        # Check subcorpus conditions
        subcorpus_conds = payload["subcorpus"]["sectionValues"][0]["conditionValues"]
        assert len(subcorpus_conds) >= 2
