"""Unit tests for Config class."""

import pytest
from rnc_mcp.config import Config
from rnc_mcp.schemas.schemas import RncCorpusType


@pytest.mark.unit
class TestConfig:
    """Tests for Config singleton class."""

    def test_base_url_is_set(self):
        """Test that BASE_URL is configured."""
        assert Config.BASE_URL == "https://ruscorpora.ru/api/v1"

    def test_corpora_has_13_entries(self):
        """Test that CORPORA dict contains all 13 corpus types."""
        assert len(Config.CORPORA) == 13

    def test_corpora_contains_expected_types(self):
        """Test that CORPORA contains expected corpus codes."""
        expected_codes = [
            "MAIN", "PAPER", "POETIC", "SPOKEN", "DIALECT",
            "SCHOOL", "SYNTAX", "MULTI", "ACCENT", "MULTIPARC",
            "KIDS", "CLASSICS", "BLOGS"
        ]
        for code in expected_codes:
            assert code in Config.CORPORA

    def test_get_token_success(self, mock_env_token):
        """Test get_token() returns token when set."""
        token = Config.get_token()
        assert token == "mock_token_12345"
        assert len(token) > 0

    def test_get_token_missing_raises_value_error(self, clear_env_token):
        """Test get_token() raises ValueError when token missing."""
        with pytest.raises(ValueError) as exc_info:
            Config.get_token()

        assert "RNC_API_TOKEN is not set" in str(exc_info.value)
        assert "https://ruscorpora.ru/accounts/profile/for-devs" in str(exc_info.value)

    def test_get_token_empty_string_raises_value_error(self, monkeypatch):
        """Test get_token() raises ValueError for empty string token."""
        monkeypatch.setenv("RNC_API_TOKEN", "")
        Config._RNC_TOKEN = ""

        with pytest.raises(ValueError) as exc_info:
            Config.get_token()

        assert "RNC_API_TOKEN is not set" in str(exc_info.value)

    def test_headers_includes_bearer_token(self, mock_env_token):
        """Test headers() includes Bearer authorization."""
        headers = Config.headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {mock_env_token}"
        assert headers["Authorization"].startswith("Bearer ")

    def test_headers_includes_content_type(self, mock_env_token):
        """Test headers() includes correct content-type."""
        headers = Config.headers()

        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_headers_includes_accept(self, mock_env_token):
        """Test headers() includes accept header."""
        headers = Config.headers()

        assert "Accept" in headers
        assert headers["Accept"] == "application/json"

    def test_headers_structure(self, mock_env_token):
        """Test that headers() returns complete structure."""
        headers = Config.headers()

        assert isinstance(headers, dict)
        assert len(headers) == 3
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in headers.items())


@pytest.mark.unit
class TestRncCorpusType:
    """Tests for dynamically generated RncCorpusType enum."""

    def test_enum_has_all_13_corpus_types(self):
        """Test that RncCorpusType enum has all 13 corpus types."""
        # Get all enum members
        corpus_types = list(RncCorpusType)
        assert len(corpus_types) == 13

    def test_enum_contains_main(self):
        """Test that MAIN corpus type exists."""
        assert hasattr(RncCorpusType, "MAIN")
        assert RncCorpusType.MAIN.value == "MAIN"

    def test_enum_contains_paper(self):
        """Test that PAPER corpus type exists."""
        assert hasattr(RncCorpusType, "PAPER")
        assert RncCorpusType.PAPER.value == "PAPER"

    def test_enum_contains_poetic(self):
        """Test that POETIC corpus type exists."""
        assert hasattr(RncCorpusType, "POETIC")
        assert RncCorpusType.POETIC.value == "POETIC"

    def test_enum_values_match_config_keys(self):
        """Test that enum values match Config.CORPORA keys."""
        corpus_types = {member.value for member in RncCorpusType}
        config_keys = set(Config.CORPORA.keys())
        assert corpus_types == config_keys

    def test_enum_member_access(self):
        """Test accessing enum members."""
        # Access by attribute
        main = RncCorpusType.MAIN
        assert main.value == "MAIN"

        # Access by value
        paper = RncCorpusType("PAPER")
        assert paper == RncCorpusType.PAPER
