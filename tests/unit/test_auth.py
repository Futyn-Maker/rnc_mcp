"""Unit tests for auth module."""

import time

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from rnc_mcp.auth.rnc_validator import RNCTokenValidator
from rnc_mcp.auth.rnc_provider import RNCAuthProvider


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCTokenValidator:
    """Tests for RNCTokenValidator."""

    async def test_valid_token(self):
        """Valid token returns True."""
        validator = RNCTokenValidator()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = True

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            result = await validator.validate("good_token")

        assert result is True

    async def test_invalid_token(self):
        """Invalid token returns False."""
        validator = RNCTokenValidator()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = False

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            result = await validator.validate(
                "bad_token"
            )

        assert result is False

    async def test_401_returns_false(self):
        """401 response returns False."""
        validator = RNCTokenValidator()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = None

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            result = await validator.validate(
                "expired_token"
            )

        assert result is False

    async def test_empty_token_returns_false(self):
        """Empty token returns False without API call."""
        validator = RNCTokenValidator()
        result = await validator.validate("")
        assert result is False

    async def test_whitespace_token_returns_false(self):
        """Whitespace-only token returns False."""
        validator = RNCTokenValidator()
        result = await validator.validate("   ")
        assert result is False

    async def test_network_error_returns_false(self):
        """Network error returns False."""
        validator = RNCTokenValidator()

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception(
                "Connection refused"
            )
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            result = await validator.validate(
                "some_token"
            )

        assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCTokenValidatorCache:
    """Tests for TTL cache in RNCTokenValidator."""

    async def test_cache_hit_skips_api_call(self):
        """Cached valid token skips API call."""
        validator = RNCTokenValidator(cache_ttl=60)
        # Pre-populate cache
        validator._cache["cached_tok"] = (True, time.time())

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            result = await validator.validate(
                "cached_tok"
            )
            mock_client_cls.assert_not_called()

        assert result is True

    async def test_cache_expired_makes_api_call(self):
        """Expired cache entry triggers API call."""
        validator = RNCTokenValidator(cache_ttl=1)
        # Pre-populate with expired entry
        validator._cache["old_tok"] = (
            True, time.time() - 10,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = False

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            result = await validator.validate("old_tok")

        # Token was previously valid, now invalid
        assert result is False
        mock_client.get.assert_called_once()

    async def test_cache_stores_result(self):
        """Validation result is stored in cache."""
        validator = RNCTokenValidator(cache_ttl=60)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = True

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            await validator.validate("new_tok")

        assert "new_tok" in validator._cache
        is_valid, _ = validator._cache["new_tok"]
        assert is_valid is True

    async def test_invalid_token_cached(self):
        """Invalid token result is also cached."""
        validator = RNCTokenValidator(cache_ttl=60)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = False

        with patch(
            "rnc_mcp.auth.rnc_validator.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            await validator.validate("bad_tok")

        is_valid, _ = validator._cache["bad_tok"]
        assert is_valid is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCAuthProvider:
    """Tests for RNCAuthProvider."""

    async def test_valid_token_returns_access_token(
        self,
    ):
        """Valid token returns AccessToken with raw
        token stored."""
        mock_validator = AsyncMock()
        mock_validator.validate.return_value = True

        provider = RNCAuthProvider(mock_validator)
        result = await provider.verify_token(
            "user_token_123"
        )

        assert result is not None
        assert result.token == "user_token_123"
        assert result.client_id == "rnc-user"
        assert "rnc:search" in result.scopes

    async def test_invalid_token_returns_none(self):
        """Invalid token returns None."""
        mock_validator = AsyncMock()
        mock_validator.validate.return_value = False

        provider = RNCAuthProvider(mock_validator)
        result = await provider.verify_token(
            "bad_token"
        )

        assert result is None

    async def test_empty_token_returns_none(self):
        """Empty token returns None without calling
        validator."""
        mock_validator = AsyncMock()

        provider = RNCAuthProvider(mock_validator)
        result = await provider.verify_token("")

        assert result is None
        mock_validator.validate.assert_not_called()

    async def test_whitespace_token_returns_none(self):
        """Whitespace token returns None."""
        mock_validator = AsyncMock()

        provider = RNCAuthProvider(mock_validator)
        result = await provider.verify_token("   ")

        assert result is None
        mock_validator.validate.assert_not_called()
