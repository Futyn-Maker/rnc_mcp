"""Unit tests for the OAuth provider."""

import time

import pytest
from unittest.mock import AsyncMock
from cryptography.fernet import Fernet

from mcp.server.auth.provider import (
    AuthorizationParams,
)
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyHttpUrl

from rnc_mcp.auth.oauth_provider import RNCOAuthProvider
from rnc_mcp.auth.token_store import TokenStore


TOKEN = "valid_rnc_token_123"
BASE_URL = "http://localhost:8000"


@pytest.fixture
def fernet_key():
    return Fernet.generate_key()


@pytest.fixture
def store(tmp_path, fernet_key):
    db_path = tmp_path / "test_oauth.db"
    return TokenStore(
        database_url=f"sqlite:///{db_path}",
        fernet_key=fernet_key,
    )


@pytest.fixture
def mock_validator():
    v = AsyncMock()
    v.validate = AsyncMock(return_value=True)
    return v


@pytest.fixture
def provider(store, mock_validator):
    return RNCOAuthProvider(
        store=store,
        rnc_validator=mock_validator,
        base_url=BASE_URL,
    )


@pytest.fixture
def client_info():
    return OAuthClientInformationFull(
        client_id="test-client-id",
        client_secret="test-secret",
        redirect_uris=[
            AnyHttpUrl("http://localhost/callback")
        ],
    )


@pytest.fixture
def auth_params():
    return AuthorizationParams(
        state="random_state_123",
        scopes=["rnc:search"],
        code_challenge="test_challenge_abc",
        redirect_uri=AnyHttpUrl(
            "http://localhost/callback"
        ),
        redirect_uri_provided_explicitly=True,
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCOAuthProviderRegistration:
    """Tests for client registration."""

    async def test_register_and_get_client(
        self, provider, client_info
    ):
        await provider.register_client(client_info)
        result = await provider.get_client(
            "test-client-id"
        )
        assert result is not None
        assert result.client_id == "test-client-id"

    async def test_get_nonexistent_client(
        self, provider
    ):
        result = await provider.get_client("nope")
        assert result is None

    async def test_register_requires_client_id(
        self, provider
    ):
        info = OAuthClientInformationFull(
            client_id=None,
            redirect_uris=[
                AnyHttpUrl("http://localhost/cb")
            ],
        )
        with pytest.raises(ValueError):
            await provider.register_client(info)


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCOAuthProviderAuthorize:
    """Tests for the authorize step."""

    async def test_authorize_returns_login_url(
        self, provider, client_info, auth_params
    ):
        await provider.register_client(client_info)
        url = await provider.authorize(
            client_info, auth_params
        )
        assert url.startswith(
            f"{BASE_URL}/login?txn="
        )

    async def test_authorize_creates_pending_auth(
        self, provider, client_info, auth_params
    ):
        await provider.register_client(client_info)
        url = await provider.authorize(
            client_info, auth_params
        )
        txn_id = url.split("txn=")[1]
        pending = provider._store.get_pending_auth(
            txn_id
        )
        assert pending is not None
        assert pending.client_id == "test-client-id"
        assert pending.state == "random_state_123"
        assert pending.code_challenge == (
            "test_challenge_abc"
        )


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCOAuthProviderCodeExchange:
    """Tests for authorization code exchange."""

    async def _create_auth_code(
        self, provider, store, client_info, auth_params
    ):
        """Helper: simulate the full authorize + login
        flow to get an auth code."""
        await provider.register_client(client_info)
        url = await provider.authorize(
            client_info, auth_params
        )
        txn_id = url.split("txn=")[1]

        # Simulate login form submission
        pending = store.consume_pending_auth(txn_id)
        import secrets

        from rnc_mcp.auth.token_store import (
            AUTH_CODE_EXPIRY,
            AuthCodeRecord,
        )

        code_value = secrets.token_urlsafe(32)
        encrypted = store.encrypt_rnc_token(TOKEN)
        store.save_auth_code(
            AuthCodeRecord(
                code=code_value,
                client_id=pending.client_id,
                scopes=pending.scopes,
                expires_at=(
                    time.time() + AUTH_CODE_EXPIRY
                ),
                code_challenge=pending.code_challenge,
                redirect_uri=pending.redirect_uri,
                redirect_uri_provided_explicitly=(
                    pending.redirect_uri_provided_explicitly
                ),
                rnc_token_encrypted=encrypted,
            )
        )
        return code_value

    async def test_exchange_code_returns_tokens(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        code = await self._create_auth_code(
            provider, store, client_info, auth_params
        )
        auth_code = await provider.load_authorization_code(
            client_info, code
        )
        assert auth_code is not None

        token = await provider.exchange_authorization_code(
            client_info, auth_code
        )
        assert token.access_token
        assert token.refresh_token
        assert token.token_type == "Bearer"
        assert token.expires_in > 0

    async def test_code_consumed_after_exchange(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        code = await self._create_auth_code(
            provider, store, client_info, auth_params
        )
        auth_code = await provider.load_authorization_code(
            client_info, code
        )
        await provider.exchange_authorization_code(
            client_info, auth_code
        )
        # Code should be consumed
        assert store.get_auth_code(code) is None

    async def test_rnc_token_recoverable_from_access_token(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        code = await self._create_auth_code(
            provider, store, client_info, auth_params
        )
        auth_code = await provider.load_authorization_code(
            client_info, code
        )
        oauth_token = (
            await provider.exchange_authorization_code(
                client_info, auth_code
            )
        )

        # Resolve back to RNC token
        rnc_token = provider.resolve_rnc_token(
            oauth_token.access_token
        )
        assert rnc_token == TOKEN

    async def test_load_code_wrong_client(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        code = await self._create_auth_code(
            provider, store, client_info, auth_params
        )
        other_client = OAuthClientInformationFull(
            client_id="other-client",
            redirect_uris=[
                AnyHttpUrl("http://localhost/cb")
            ],
        )
        result = (
            await provider.load_authorization_code(
                other_client, code
            )
        )
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCOAuthProviderRefresh:
    """Tests for refresh token exchange."""

    async def _issue_tokens(
        self, provider, store, client_info, auth_params
    ):
        """Helper: full flow to get access + refresh."""
        await provider.register_client(client_info)
        url = await provider.authorize(
            client_info, auth_params
        )
        txn_id = url.split("txn=")[1]
        pending = store.consume_pending_auth(txn_id)

        import secrets

        from rnc_mcp.auth.token_store import (
            AUTH_CODE_EXPIRY,
            AuthCodeRecord,
        )

        code_value = secrets.token_urlsafe(32)
        encrypted = store.encrypt_rnc_token(TOKEN)
        store.save_auth_code(
            AuthCodeRecord(
                code=code_value,
                client_id=pending.client_id,
                scopes=pending.scopes,
                expires_at=(
                    time.time() + AUTH_CODE_EXPIRY
                ),
                code_challenge=pending.code_challenge,
                redirect_uri=pending.redirect_uri,
                redirect_uri_provided_explicitly=(
                    pending.redirect_uri_provided_explicitly
                ),
                rnc_token_encrypted=encrypted,
            )
        )
        auth_code = (
            await provider.load_authorization_code(
                client_info, code_value
            )
        )
        return (
            await provider.exchange_authorization_code(
                client_info, auth_code
            )
        )

    async def test_refresh_returns_new_tokens(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        oauth = await self._issue_tokens(
            provider, store, client_info, auth_params
        )
        rt = await provider.load_refresh_token(
            client_info, oauth.refresh_token
        )
        assert rt is not None

        new_oauth = await provider.exchange_refresh_token(
            client_info, rt, ["rnc:search"]
        )
        assert new_oauth.access_token != (
            oauth.access_token
        )
        assert new_oauth.refresh_token != (
            oauth.refresh_token
        )

    async def test_refresh_preserves_rnc_token(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        oauth = await self._issue_tokens(
            provider, store, client_info, auth_params
        )
        rt = await provider.load_refresh_token(
            client_info, oauth.refresh_token
        )
        new_oauth = await provider.exchange_refresh_token(
            client_info, rt, ["rnc:search"]
        )
        rnc = provider.resolve_rnc_token(
            new_oauth.access_token
        )
        assert rnc == TOKEN

    async def test_old_tokens_revoked_after_refresh(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        oauth = await self._issue_tokens(
            provider, store, client_info, auth_params
        )
        old_at = oauth.access_token
        old_rt = oauth.refresh_token
        rt = await provider.load_refresh_token(
            client_info, old_rt
        )
        await provider.exchange_refresh_token(
            client_info, rt, ["rnc:search"]
        )
        assert store.get_access_token(old_at) is None
        assert store.get_refresh_token(old_rt) is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCOAuthProviderDualAuth:
    """Tests for dual authentication (OAuth + direct
    bearer)."""

    async def test_oauth_token_verified(
        self,
        provider,
        store,
        client_info,
        auth_params,
    ):
        """OAuth-issued tokens are verified via store."""
        await provider.register_client(client_info)
        url = await provider.authorize(
            client_info, auth_params
        )
        txn_id = url.split("txn=")[1]
        pending = store.consume_pending_auth(txn_id)

        import secrets

        from rnc_mcp.auth.token_store import (
            AUTH_CODE_EXPIRY,
            AuthCodeRecord,
        )

        code_value = secrets.token_urlsafe(32)
        store.save_auth_code(
            AuthCodeRecord(
                code=code_value,
                client_id=pending.client_id,
                scopes=pending.scopes,
                expires_at=(
                    time.time() + AUTH_CODE_EXPIRY
                ),
                code_challenge=pending.code_challenge,
                redirect_uri=pending.redirect_uri,
                redirect_uri_provided_explicitly=(
                    pending.redirect_uri_provided_explicitly
                ),
                rnc_token_encrypted=(
                    store.encrypt_rnc_token(TOKEN)
                ),
            )
        )
        auth_code = (
            await provider.load_authorization_code(
                client_info, code_value
            )
        )
        oauth = (
            await provider.exchange_authorization_code(
                client_info, auth_code
            )
        )

        result = await provider.load_access_token(
            oauth.access_token
        )
        assert result is not None
        assert result.client_id == "test-client-id"

    async def test_direct_rnc_token_verified(
        self, provider, mock_validator
    ):
        """Raw RNC token falls back to validator."""
        mock_validator.validate.return_value = True
        result = await provider.load_access_token(
            "raw_rnc_token_xyz"
        )
        assert result is not None
        assert result.client_id == "rnc-direct"
        mock_validator.validate.assert_called_with(
            "raw_rnc_token_xyz"
        )

    async def test_invalid_direct_token_rejected(
        self, provider, mock_validator
    ):
        """Invalid raw token returns None."""
        mock_validator.validate.return_value = False
        result = await provider.load_access_token(
            "bad_token"
        )
        assert result is None

    async def test_resolve_oauth_token(
        self, provider, store
    ):
        """OAuth token resolves to encrypted RNC token."""
        from rnc_mcp.auth.token_store import TokenRecord

        encrypted = store.encrypt_rnc_token(TOKEN)
        store.save_access_token(
            TokenRecord(
                token="oauth_at",
                client_id="c1",
                scopes=["rnc:search"],
                expires_at=int(time.time() + 3600),
                rnc_token_encrypted=encrypted,
            )
        )
        result = provider.resolve_rnc_token("oauth_at")
        assert result == TOKEN

    async def test_resolve_direct_bearer(
        self, provider
    ):
        """Direct bearer token resolves to itself."""
        result = provider.resolve_rnc_token(
            "direct_rnc_token"
        )
        assert result == "direct_rnc_token"


@pytest.mark.unit
@pytest.mark.asyncio
class TestRNCOAuthProviderRevocation:
    """Tests for token revocation."""

    async def test_revoke_access_token(
        self, provider, store
    ):
        from rnc_mcp.auth.token_store import TokenRecord

        encrypted = store.encrypt_rnc_token("rnc")
        store.save_access_token(
            TokenRecord(
                token="revoke_at",
                client_id="c1",
                scopes=[],
                expires_at=int(time.time() + 3600),
                rnc_token_encrypted=encrypted,
            )
        )
        at = await provider.load_access_token(
            "revoke_at"
        )
        await provider.revoke_token(at)
        assert (
            store.get_access_token("revoke_at") is None
        )
